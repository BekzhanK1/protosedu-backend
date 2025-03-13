from django.contrib.auth.models import AnonymousUser
from django.db import transaction
from rest_framework import serializers

from .models import DURATION_CHOICES, Payment, Plan, Subscription


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ["price", "duration", "is_enabled"]


class SubscriptionModelSerializer(serializers.ModelSerializer):
    plan = serializers.CharField(source="plan.duration", read_only=True)

    class Meta:
        model = Subscription
        fields = ["user", "plan", "start_date", "end_date", "is_active"]


class SubscriptionCreateSerializer(serializers.Serializer):
    plan_name = serializers.CharField(max_length=20)

    def validate(self, data):
        plan_name = data.get("plan_name")

        if plan_name not in dict(DURATION_CHOICES) or plan_name == "free-trial":
            raise serializers.ValidationError("Invalid plan name.")

        plan = Plan.objects.filter(duration=plan_name, is_enabled=True).first()
        if not plan:
            raise serializers.ValidationError("Invalid plan name.")

        data["user"] = self.context["user"]
        data["plan"] = plan
        return data

    def create(self, validated_data):
        user = self.context["request"].user

        if isinstance(user, AnonymousUser):
            user = validated_data["user"]

        plan = validated_data["plan"]
        active_subscription = Subscription.objects.filter(user=user).first()

        try:
            with transaction.atomic():
                if active_subscription:
                    if active_subscription.plan.duration == "free-trial":
                        active_subscription.delete()
                        return self._create_subscription(user, plan)
                    elif active_subscription.is_active:
                        raise serializers.ValidationError(
                            "You already have an active subscription."
                        )
                return self._create_subscription(user, plan)

        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})

    def _create_subscription(self, user, plan):
        return Subscription.objects.create(user=user, plan=plan)


class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        fields = "__all__"
        model = Payment
