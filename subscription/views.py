from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from account.permissions import IsParent, IsStudent, IsSuperUser
from .models import Plan, Subscription
from .serializers import PlanSerializer, SubscriptionSerializer, SubscriptionCreateSerializer

class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Plan.objects.filter(is_enabled=True)
    serializer_class = PlanSerializer

class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == 'create':
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
        plan_name = request.data.get('plan_name')
        serializer = SubscriptionCreateSerializer(data={'plan_name': plan_name}, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        raise PermissionDenied("You do not have permission to update subscriptions.")

    def destroy(self, request, *args, **kwargs):
        raise PermissionDenied("You do not have permission to delete subscriptions.")

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Subscription.objects.all()
        return Subscription.objects.filter(user=self.request.user)
