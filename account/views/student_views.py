from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.response import Response

from account.models import Class, Student
from account.permissions import IsSuperUser
from account.serializers import StudentRegistrationSerializer, StudentSerializer


class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [IsSuperUser]

    def get_queryset(self):
        return Student.objects.filter(school_class_id=self.kwargs["class_pk"])

    def create(self, request, *args, **kwargs):
        school_id = self.kwargs["school_pk"]
        class_id = self.kwargs["class_pk"]
        school_class = get_object_or_404(Class, pk=class_id)
        data = request.data.copy()
        data["school"] = school_id
        data["school_class"] = class_id
        data["grade"] = school_class.grade
        data["language"] = school_class.language

        serializer = StudentRegistrationSerializer(data=data)
        if serializer.is_valid():
            student = serializer.save()
            return Response(
                {
                    "message": f"Activation email has been sent to {data['email']}",
                    "student_id": student.pk,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
