from datetime import timedelta

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from account.models import User

DURATION_CHOICES = [
    ("free-trial", "Free Trial"),
    ("monthly", "Monthly"),
    ("6-month", "6 Month"),
    ("annual", "Annual"),
]

MAX_FREE_TRIAL_QUESTIONS = 10


class Plan(models.Model):
    price = models.DecimalField(max_digits=7, decimal_places=0, blank=True, null=True)
    duration = models.CharField(max_length=10, choices=DURATION_CHOICES, unique=True)
    is_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_duration_display()} Plan"


class Subscription(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="subscription"
    )
    plan = models.ForeignKey(
        Plan, on_delete=models.CASCADE, related_name="subscriptions"
    )
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.start_date:
            self.start_date = timezone.now()

        if not self.end_date:
            self.end_date = self.calculate_end_date()
        super().save(*args, **kwargs)

    def calculate_end_date(self):
        if self.plan.duration == "free-trial":
            return self.start_date + timedelta(days=2)
        elif self.plan.duration == "monthly":
            return self.start_date + timedelta(days=30)
        elif self.plan.duration == "6-month":
            return self.start_date + timedelta(days=180)
        elif self.plan.duration == "annual":
            return self.start_date + timedelta(days=365)
        return None

    def is_free_trial(self):
        return self.plan.duration == "free-trial"

    @property
    def is_active(self):
        if self.is_free_trial():
            return self.is_free_trial_active()
        return self.end_date is not None and timezone.now() < self.end_date

    def is_free_trial_active(self):
        if not self.user.is_parent:
            return False
        children = self.user.parent.children.all()
        if not children.exists():
            return True
        for child in children:
            if child.answers.count() >= MAX_FREE_TRIAL_QUESTIONS:
                return False
        return True

    def __str__(self):
        return (
            f"{self.user.email} - {self.plan.duration} Plan (Expires: {self.end_date})"
        )


class Payment(models.Model):
    invoice_id = models.CharField(max_length=15, unique=True)
    invoice_id_alt = models.CharField(max_length=15, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments")
    amount = models.IntegerField(
        validators=[
            MaxValueValidator(99999),
            MinValueValidator(0),
        ]
    )
    duration = models.CharField(max_length=10, choices=DURATION_CHOICES)
    currency = models.CharField(max_length=3, default="KZT")
    status = models.CharField(
        max_length=20,
        choices=[
            ("initiated", "Initiated"),
            ("pending", "Pending"),
            ("success", "Success"),
            ("failed", "Failed"),
        ],
        default="initiated",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"Payment {self.invoice_id} - {self.status}"

    class Meta:
        ordering = ["-created_at"]  # Default ordering by creation date, newest first
