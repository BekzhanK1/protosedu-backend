from django.contrib import admin

from .models import Payment, Plan, Subscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("duration", "price", "is_enabled")
    search_fields = ("duration",)
    list_filter = ("is_enabled",)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "start_date", "end_date", "is_active")
    search_fields = ("user__email", "plan__duration", "user__username")
    ordering = ("-start_date",)
    list_filter = ("plan__duration", "start_date", "end_date")
    raw_id_fields = ("user", "plan")

    def is_active(self, obj):
        return obj.is_active

    is_active.boolean = True
    is_active.short_description = "Is Active"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_id",
        "user",
        "duration",
        "amount",
        "currency",
        "status",
        "created_at",
        "updated_at",
    )
    search_fields = ("invoice_id", "user__email", "status")
    list_filter = ("status", "currency", "created_at", "updated_at")
    raw_id_fields = ("user",)
    readonly_fields = (
        "email",
        "currency",
        "amount",
        "user",
        "status",
        "invoice_id",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        # Disallow adding payments manually through the admin interface
        return False

    def has_delete_permission(self, request, obj=None):
        # Disallow deleting payments through the admin interface
        return True
