from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated


class IsTestUser(IsAuthenticated):
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        return is_authenticated and request.user.is_test_user


class IsSuperUser(IsAuthenticated):
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        return is_authenticated and request.user.is_superuser


class IsParent(IsAuthenticated):
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        return is_authenticated and request.user.is_parent


class IsStudent(IsAuthenticated):
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        return is_authenticated and request.user.is_student


class IsStaff(IsAuthenticated):
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        return is_authenticated and request.user.is_staff


class IsSuperUserOrStaffOrReadOnly(IsAuthenticated):
    """
    Custom permission to only allow superusers or staff to edit it.
    Read permissions are allowed to any authenticated user.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and (request.user.is_superuser or request.user.is_staff)


class IsSupervisor(IsAuthenticated):
    def has_permission(self, request, view):
        return request.user and request.user.is_supervisor


class HasSubscription(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        print(f"User: {request.user}, Is Test User: {request.user.is_test_user}")
        if request.user.is_test_user:
            return True

        if request.user.is_student or request.user.is_parent:
            if not hasattr(request.user, "subscription"):
                raise PermissionDenied("You do not have an active subscription.")

            if not request.user.subscription.is_active:
                raise PermissionDenied("You do not have an active subscription.")

        return True
