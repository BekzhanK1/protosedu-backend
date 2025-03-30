from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction

from account.models import Class, LANGUAGE_CHOICES
from account.permissions import IsSuperUser
from account.serializers import ClassSerializer


class ClassViewSet(viewsets.ModelViewSet):
    serializer_class = ClassSerializer
    permission_classes = [IsSuperUser]

    def get_queryset(self):
        return Class.objects.filter(school_id=self.kwargs["school_pk"]).order_by(
            "grade"
        )

    def create(self, request, *args, **kwargs):
        school_id = self.kwargs["school_pk"]
        data = request.data.copy()
        data["school"] = school_id

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            school_class = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["patch"], permission_classes=[IsSuperUser])
    def change_language(self, request, *args, **kwargs):
        school_class = self.get_object()
        new_language = request.data.get("language")
        # Check if the new language is valid
        valid_languages = [choice[0] for choice in LANGUAGE_CHOICES]
        if new_language not in valid_languages:
            return Response(
                {"error": "invalid language"}, status=status.HTTP_400_BAD_REQUEST
            )
        if new_language:
            if new_language == school_class.language:
                return Response(
                    {"error": "language already set to this value"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            with transaction.atomic():
                for student in school_class.students.all():
                    student.language = new_language
                    student.save()
                school_class.language = new_language
                school_class.save()

            return Response(
                {"status": f"language updated to {new_language}"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": "language not provided"}, status=status.HTTP_400_BAD_REQUEST
        )
