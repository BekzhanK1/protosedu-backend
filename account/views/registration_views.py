from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from account.permissions import IsSuperUser
from account.serializers import (
    ParentRegistrationSerializer,
    StaffRegistrationSerializer,
)


class StaffRegistrationAPIView(APIView):
    permission_classes = [IsSuperUser]

    def post(self, request):
        data = request.data
        data["role"] = "staff"
        serializer = StaffRegistrationSerializer(data=data)
        if serializer.is_valid():
            staff = serializer.save()
            return Response(
                {
                    "message": "Staff user is registered successfully",
                    "staff_id": staff.pk,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ParentRegistrationAPIView(APIView):
    def post(self, request):
        data = request.data
        serializer = ParentRegistrationSerializer(data=data)
        if serializer.is_valid():
            parent = serializer.save()
            return Response(
                {
                    "message": f"Activation email sent to {data['email']}",
                    "parent_id": parent.pk,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
