from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from account.models import Child, Student
from account.serializers import ChildSerializer


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        cache_key = f"user_data_{user.id}"
        cached_data = cache.get(cache_key)

        print("cached_data", cached_data)

        if cached_data is None:
            print("cached_data is None")
            data = self._get_user_data(user)
            cache.set(cache_key, data, timeout=300)  # Cache for 5 minutes
        else:
            data = cached_data

        return Response(data)

    def _get_user_data(self, user):
        data = {}
        has_subscription = hasattr(user, "subscription")
        active_subscription = user.subscription if has_subscription else None
        is_free_trial = False
        subscription_active = (
            active_subscription.is_active if active_subscription else False
        )
        if active_subscription:
            is_free_trial = active_subscription.plan.duration == "free-trial"

        if user.is_student:
            data["user"] = self._get_student_data(
                user, subscription_active, is_free_trial
            )
        elif user.is_parent:
            data["user"] = self._get_parent_data(
                user, subscription_active, is_free_trial
            )
        elif user.is_supervisor:
            data["user"] = self._get_supervisor_data(user)
        else:
            data["user"] = self._get_superadmin_data(user)
        return data

    def _get_student_data(self, user, subscription_active, is_free_trial):
        student = Student.objects.get(user=user)
        tasks_completed = user.completed_tasks.count()
        print(user.is_test_user)
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "grade": student.grade,
            "gender": student.gender,
            "language": student.language,
            "level": student.level,
            "streak": student.streak,
            "cups": student.cups,
            "stars": student.stars,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
            "tasks_completed": tasks_completed,
            "has_subscription": True if user.is_test_user else subscription_active,
            "is_free_trial": is_free_trial,
            "requires_password_change": user.requires_password_change,
        }

    def _get_parent_data(self, user, subscription_active, is_free_trial):
        parent = user.parent
        children = Child.objects.filter(parent=parent)
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "children": ChildSerializer(children, many=True).data,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
            "has_subscription": subscription_active,
            "is_free_trial": is_free_trial,
        }

    def _get_supervisor_data(self, user):
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
        }

    def _get_superadmin_data(self, user):
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": "superadmin",
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
        }


class UserUpdateView(APIView):
    def patch(self, request):
        user = request.user
        data = request.data
        child_id = request.query_params.get("child_id", None)

        if not child_id:
            self._update_user(user, data)
        else:
            child = get_object_or_404(Child, pk=child_id, parent=user.parent)
            self._update_child(child, data)

        return Response(status=status.HTTP_204_NO_CONTENT)

    def _update_user(self, user, data):
        updated = False
        if "first_name" in data and data["first_name"] != user.first_name:
            user.first_name = data["first_name"]
            updated = True
        if "last_name" in data and data["last_name"] != user.last_name:
            user.last_name = data["last_name"]
            updated = True
        if "phone_number" in data and data["phone_number"] != user.phone_number:
            user.phone_number = data["phone_number"]
            updated = True

        if user.is_student:
            student = user.student
            if "language" in data and data["language"] != student.language:
                student.language = data["language"]
                student.save()
                updated = True
            if "avatar" in data and data["avatar"] != student.avatar:
                student.avatar = data["avatar"]
                student.save()
                updated = True

        if updated:
            user.save()

    def _update_child(self, child, data):
        updated = False
        if "first_name" in data and data["first_name"] != child.first_name:
            child.first_name = data["first_name"]
            updated = True
        if "last_name" in data and data["last_name"] != child.last_name:
            child.last_name = data["last_name"]
            updated = True
        if "grade" in data and data["grade"] != child.grade:
            child.grade = data["grade"]
            updated = True
        if "avatar" in data and data["avatar"] != child.avatar:
            child.avatar = data["avatar"]
            updated = True

        if updated:
            child.save()
