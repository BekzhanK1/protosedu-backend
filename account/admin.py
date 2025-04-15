from datetime import date, timedelta

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    Child,
    Class,
    LevelRequirement,
    Parent,
    School,
    Student,
    User,
    MotivationalPhrase,
    DailyMessage,
)

##############################
# USER ADMIN IMPROVEMENTS
##############################


class CustomUserAdmin(BaseUserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "is_active",
        "is_staff",
        "is_superuser",
    )
    list_filter = ("is_active", "is_staff", "is_superuser", "role")
    search_fields = (
        "username__icontains",
        "email__icontains",
        "first_name__icontains",
        "last_name__icontains",
    )
    ordering = ("username",)
    filter_horizontal = ()  # add if you have many-to-many fields

    def save_model(self, request, obj, form, change):
        # Always ensure that password is stored hashed only when changed.
        if change:
            if "password" in form.changed_data:
                obj.password = make_password(obj.password)
        else:
            obj.password = make_password(obj.password)
        super().save_model(request, obj, form, change)


admin.site.register(User, CustomUserAdmin)

##############################
# CHILD ADMIN & INLINE
##############################


class ChildInline(admin.TabularInline):
    model = Child
    extra = 0
    fields = (
        "first_name",
        "last_name",
        "grade",
        "level",
        "streak",
        "cups",
        "stars",
        "language",
    )
    readonly_fields = ()


@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "grade",
        "level",
        "streak",
        "cups",
        "stars",
        "parent_email",
    )
    search_fields = ("first_name", "last_name", "parent__user__email")
    list_filter = ("grade", "level", "gender", "language")
    raw_id_fields = ("parent",)
    ordering = ("first_name", "last_name")

    def parent_email(self, obj):
        return obj.parent.user.email

    parent_email.short_description = "Parent Email"


##############################
# PARENT ADMIN WITH CHILD INLINE
##############################


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "user_username",
        "user_first_name",
        "user_last_name",
        "user_email",
    )
    search_fields = ("user__first_name", "user__last_name", "user__email")
    ordering = ("user__username",)
    inlines = [ChildInline]

    def user_username(self, obj):
        return obj.user.username

    user_username.short_description = "Username"

    def user_first_name(self, obj):
        return obj.user.first_name

    user_first_name.short_description = "First Name"

    def user_last_name(self, obj):
        return obj.user.last_name

    user_last_name.short_description = "Last Name"

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "Email"


##############################
# STUDENT ADMIN IMPROVEMENTS
##############################


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "user_full_name",
        "user",
        "school",
        "school_class",
        "grade",
        "level",
        "streak",
        "cups",
        "stars",
    )
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email",
        "school__name",
        "school_class__grade",
    )
    list_filter = ("grade", "level", "gender", "language")
    raw_id_fields = ("user", "school", "school_class")
    ordering = ("user__username",)

    def user_full_name(self, obj):
        return obj.user.get_full_name()

    user_full_name.short_description = "Full Name"


##############################
# CLASS ADMIN IMPROVEMENTS WITH INLINE FOR SCHOOL
##############################


class ClassInline(admin.TabularInline):
    model = Class
    extra = 0
    fields = ("grade", "section", "language")
    readonly_fields = ()


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ("school", "grade", "section", "language")
    search_fields = ("school__name", "grade", "section")
    list_filter = ("grade", "language")
    raw_id_fields = ("school",)
    ordering = ("school", "grade", "section")


##############################
# LEVEL REQUIREMENT ADMIN
##############################


@admin.register(LevelRequirement)
class LevelRequirementAdmin(admin.ModelAdmin):
    list_display = ("level", "cups_required")
    search_fields = ("level",)
    list_filter = ("level",)
    ordering = ("level",)


##############################
# SCHOOL ADMIN WITH CLASS INLINE
##############################


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "email", "supervisor_email")
    search_fields = ("name", "city", "email", "supervisor__email")
    list_filter = ("city",)
    raw_id_fields = ("supervisor",)
    inlines = [ClassInline]
    ordering = ("name",)

    def supervisor_email(self, obj):
        return obj.supervisor.email if obj.supervisor else "-"

    supervisor_email.short_description = "Supervisor Email"


##############################
# MOTIVATIONAL PHRASE ADMIN
##############################


@admin.register(MotivationalPhrase)
class MotivationalPhraseAdmin(admin.ModelAdmin):
    list_display = ("text", "language", "is_active", "created_at", "updated_at")
    search_fields = ("text",)
    list_filter = ("language", "is_active")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")


##############################
# DAILY MESSAGE ADMIN
##############################


@admin.register(DailyMessage)
class DailyMessageAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "message_short",
        "language",
        "is_active",
        "created_at",
        "updated_at",
    )
    search_fields = ("message",)
    list_filter = ("language", "is_active", "date")
    ordering = ("-date",)
    date_hierarchy = "date"
    readonly_fields = ("created_at", "updated_at")

    def message_short(self, obj):
        # Show the first 50 characters of the message for brevity
        return f"{obj.message[:50]}..." if len(obj.message) > 50 else obj.message

    message_short.short_description = "Message"
