import uuid
from datetime import timedelta

from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from account.models import User
from account.serializers import MyTokenObtainPairSerializer
from subscription.models import Plan, Subscription

from ..tasks import send_activation_email, send_password_reset_request_email
from ..utils import generate_password


class ActivateAccount(APIView):

    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            user = User.objects.get(activation_token=token)
            if user.is_activation_token_expired:
                with transaction.atomic():
                    user.activation_token = uuid.uuid4()
                    user.activation_token_expires_at = timezone.now() + timedelta(
                        days=1
                    )
                    user.save()
                    send_activation_email.delay(user.pk, generate_password())
                return Response(
                    "Your activation link has expired! You will receive a new email soon",
                    status=status.HTTP_403_FORBIDDEN,
                )
            with transaction.atomic():
                user.is_active = True
                user.activation_token = None
                user.save()
                if user.is_parent:
                    plan, _ = Plan.objects.get_or_create(duration="free-trial")
                    Subscription.objects.create(user=user, plan=plan)
                elif user.is_student:
                    plan, _ = Plan.objects.get_or_create(duration="annual")
                    Subscription.objects.create(user=user, plan=plan)
            return Response(
                "Your account has been activated successfully!",
                status=status.HTTP_200_OK,
            )
        except User.DoesNotExist:
            return Response(
                "Invalid activation link!", status=status.HTTP_400_BAD_REQUEST
            )


class ChangePassword(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        current_password = request.data["current_password"]
        new_password = request.data["new_password"]
        auth_user = authenticate(email=user.email, password=current_password)
        if auth_user:
            try:
                auth_user.set_password(new_password)
                auth_user.save()
                return Response(
                    {"message": "Successfully changed password"},
                    status=status.HTTP_200_OK,
                )
            except Exception:
                return Response(
                    {"message": "Error during password change"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                {"message": "Current password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class RequestResetPassword(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        if email and username:
            user = get_object_or_404(User, email=email, username=username)
            user.reset_password_token = uuid.uuid4()
            user.reset_password_token_expires_at = timezone.now() + timedelta(days=1)
            user.save()
            send_password_reset_request_email.delay(user.pk)
            return Response(
                {"message": "Request has been sent to email"},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {
                    "message": "You need to enter the email and username to reset the password"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class ResetPassword(APIView):
    permission_classes = [AllowAny]

    def post(self, request, token):
        try:
            user = User.objects.get(reset_password_token=token)
            if user.is_reset_password_token_expired:
                return Response(
                    "Your reset password link has expired!",
                    status=status.HTTP_403_FORBIDDEN,
                )
            password = request.data["password"]
            user.set_password(password)
            user.reset_password_token = None
            user.save()
            return Response(
                {"message": "Successfully reset password"}, status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response("Invalid reset link!", status=status.HTTP_400_BAD_REQUEST)


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
