from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.hashers import make_password
from .models import Child, Class, LevelRequirement, Parent, School, Student, User


# Register User model with customizations
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
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
    search_fields = ("username", "email", "first_name", "last_name")
    list_filter = ("is_active", "is_staff", "is_superuser", "role")


class CustomUserAdmin(UserAdmin):
    def save_model(self, request, obj, form, change):
        if change:
            if "password" in form.changed_data:
                obj.password = make_password(obj.password)
        else:
            obj.password = make_password(obj.password)
        super().save_model(request, obj, form, change)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# Register Child model with customizations
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
        "parent",
    )
    search_fields = ("first_name", "last_name", "parent__user__email")
    list_filter = ("grade", "level", "gender", "language")
    raw_id_fields = ("parent",)


# Register Parent model with customizations
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

    def user_username(self, obj):
        return obj.user.username

    def user_first_name(self, obj):
        return obj.user.first_name

    def user_last_name(self, obj):
        return obj.user.last_name

    def user_email(self, obj):
        return obj.user.email


# Register Student model with customizations
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
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
        "school__name",
        "school_class__grade",
    )
    list_filter = ("grade", "level", "gender", "language")
    raw_id_fields = ("user", "school", "school_class")


# Register Class model with customizations
@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ("school", "grade", "section", "language")
    search_fields = ("school__name", "grade", "section")
    list_filter = ("grade", "language")
    raw_id_fields = ("school",)


# Register LevelRequirement model with customizations
@admin.register(LevelRequirement)
class LevelRequirementAdmin(admin.ModelAdmin):
    list_display = ("level", "cups_required")
    search_fields = ("level",)
    list_filter = ("level",)


# Register School model with customizations
@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "email", "supervisor")
    search_fields = ("name", "city", "email", "supervisor__email")
    list_filter = ("city",)
    raw_id_fields = ("supervisor",)
