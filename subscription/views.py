import requests
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from account.permissions import IsParent, IsStudent, IsSuperUser

from .models import Payment, Plan, Subscription
from .serializers import (
    PaymentSerializer,
    PlanSerializer,
    SubscriptionCreateSerializer,
    SubscriptionModelSerializer,
)
from .utils import generate_invoice_id

TERMINAL_ID = settings.HALYK_TERMINAL_ID
CLIENT_ID = settings.HALYK_CLIENT_ID
CLIENT_SECRET = settings.HALYK_CLIENT_SECRET


class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Plan.objects.filter(is_enabled=True)
    serializer_class = PlanSerializer


class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionModelSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == "create":
            self.permission_classes = [IsParent | IsStudent]
        else:
            self.permission_classes = [IsSuperUser]
        return super().get_permissions()

    def list(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied("You do not have permission to list subscriptions.")
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = SubscriptionCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        subscription = serializer.save()
        return Response(
            self.serializer_class(subscription).data, status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        raise PermissionDenied("You do not have permission to update subscriptions.")

    def destroy(self, request, *args, **kwargs):
        raise PermissionDenied("You do not have permission to delete subscriptions.")

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Subscription.objects.all()
        return Subscription.objects.filter(user=self.request.user)


@api_view(["POST"])
def initiate_payment(request):
    user = request.user
    if not user.is_parent:
        return Response(
            {"message": "Only parents can initiate payments"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    invoice_id = generate_invoice_id()
    invoice_id_alt = generate_invoice_id()
    duration = request.data.get("duration")
    plan = get_object_or_404(
        Plan.objects.exclude(duration="free-trial"), duration=duration
    )
    amount = plan.price
    subscription = Subscription.objects.filter(user=user).first()
    if subscription:
        if not subscription.is_free_trial() and subscription.is_active:
            return Response(
                {"message": "You have active subscription"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    try:
        with transaction.atomic():
            existing_payment = Payment.objects.filter(
                user=user, status="pending", duration=duration
            ).first()

            if existing_payment:
                payment = existing_payment
            else:
                payment = Payment.objects.create(
                    invoice_id=invoice_id,
                    invoice_id_alt=invoice_id_alt,
                    user=user,
                    duration=plan.duration,
                    amount=amount,
                    email=user.email,
                )

            post_link = f"https://api.protosedu.kz/api/payments/payment-confirmation/"
            failure_post_link = (
                f"https://api.protosedu.kz/api/payments/payment-confirmation/"
            )
            payment_data = {
                "grant_type": "client_credentials",
                "scope": "webapi usermanagement email_send verification statement statistics payment",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "invoiceID": invoice_id,
                "amount": amount,
                "currency": "KZT",
                "terminal": TERMINAL_ID,
                "postLink": post_link,
                "failurePostLink": failure_post_link,
            }

            response = requests.post(
                "https://epay-oauth.homebank.kz/oauth2/token",
                data=payment_data,
            )

            if response.status_code == 200:
                payment_serializer = PaymentSerializer(payment)
                token_json = response.json()
                payment.status = "pending"
                payment.save()
                return Response(
                    {"payment": payment_serializer.data, "token": token_json}
                )

            else:
                return Response(
                    {"error": "Failed to initiate payment", "details": response.text},
                    status=status.HTTP_400_BAD_REQUEST,
                )
    except Exception as e:
        return Response(
            {"error": "Failed to initiate payment", "details": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def payment_confirmation(request):
    invoice_id = request.data.get("invoiceId")
    status_code = request.data.get("code")

    payment = get_object_or_404(Payment, invoice_id=invoice_id, status="pending")
    user = payment.user

    try:
        with transaction.atomic():
            if status_code == "ok":
                payment.status = "success"
                payment.save()

                plan_name = payment.duration
                serializer = SubscriptionCreateSerializer(
                    data={"plan_name": plan_name},
                    context={"request": request, "user": user},
                )

                if serializer.is_valid():
                    subscription = serializer.save()
                    return Response(
                        {
                            "message": "Subscription created successfully",
                            "subscription_id": subscription.id,
                        },
                        status=status.HTTP_201_CREATED,
                    )
                else:
                    return Response(
                        serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                payment.status = "failed"
                payment.save()
                return Response(
                    {"message": "Payment failed"}, status=status.HTTP_400_BAD_REQUEST
                )
    except Exception as e:
        return Response(
            {"message": "Error occurred", "details": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )
