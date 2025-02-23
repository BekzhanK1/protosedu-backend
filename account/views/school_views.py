import uuid

import pandas as pd
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from account.models import Class, School, Student, User
from account.permissions import IsSuperUser
from account.serializers import (SchoolSerializer,
                                 SupervisorRegistrationSerializer)

from ..tasks import send_mass_activation_email


class SchoolViewSet(viewsets.ModelViewSet):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [IsSuperUser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            school = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def assign_supervisor(self, request, pk=None):
        school = self.get_object()

        if school.supervisor:
            return Response(
                {"message": "School already has a supervisor"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SupervisorRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            supervisor = serializer.save()
            school.supervisor = supervisor
            school.save()
            return Response(
                {
                    "message": "Supervisor is registered successfully",
                    "supervisor_id": supervisor.pk,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"])
    def deassign_supervisor(self, request, pk=None):
        school = self.get_object()
        if not school.supervisor:
            return Response(
                {"message": "School doesn't have a supervisor"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        school.supervisor.delete()
        school.supervisor = None
        school.save()
        return Response(
            {"message": "Supervisor has been removed from the school"},
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["post"],
        url_path="upload-excel",
        url_name="upload-excel",
        permission_classes=[IsSuperUser],
    )
    def upload_excel(self, request):
        file = request.FILES.get("file")
        school_id = request.query_params.get("school_id")
        if not file:
            return Response(
                {"message": "No file was uploaded"}, status=status.HTTP_400_BAD_REQUEST
            )

        return self.parse_excel(file, school_id)

    def parse_excel(self, file, school_id):
        """
        Parses the uploaded Excel file, extracts student data,
        and checks for duplicate emails before processing further.
        """
        try:
            xls = pd.ExcelFile(file)
        except Exception as e:
            return Response(
                {"message": f"Invalid Excel file format: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        names_to_drop = ["Оқушының аты-жөні"]
        all_students = []
        email_to_students = {}
        duplicate_emails = {}

        def load_clean_sheet(sheet_name):
            df = pd.read_excel(xls, sheet_name=sheet_name, skiprows=1)

            # Rename columns
            df.columns = [
                "№",
                "Оқушының аты-жөні",
                "Параллель",
                "Литер",
                "Ата-анасының электронды почтасы",
            ]
            df[["Жөні", "Аты"]] = df["Оқушының аты-жөні"].str.split(n=2, expand=True)[
                [0, 1]
            ]
            df = df.drop(columns=["№"])
            df = df.dropna(subset=["Оқушының аты-жөні"])
            df = df.dropna(subset=["Параллель"])
            df = df.dropna(subset=["Литер"])
            df = df.dropna(subset=["Ата-анасының электронды почтасы"])
            df = df[~df["Оқушының аты-жөні"].isin(names_to_drop)]
            df = df.drop(columns=["Оқушының аты-жөні"])

            # Convert to a list of dictionaries
            students = [
                {
                    "first_name": row["Аты"],
                    "last_name": row["Жөні"],
                    "grade": row["Параллель"],
                    "section": row["Литер"],
                    "email": row["Ата-анасының электронды почтасы"],
                }
                for _, row in df.iterrows()
            ]

            return students

        # Process all sheets in the Excel file
        for sheet in xls.sheet_names:
            sheet_students = load_clean_sheet(sheet)
            all_students.extend(sheet_students)

        print(all_students)

        # Check for duplicate emails
        for student in all_students:
            email = student["email"]
            if email in email_to_students:
                if email not in duplicate_emails:
                    duplicate_emails[email] = [email_to_students[email]]
                duplicate_emails[email].append(student)
            else:
                email_to_students[email] = student

        if duplicate_emails:
            return Response(
                {
                    "message": "Duplicate emails found",
                    "num_duplicates": len(duplicate_emails),
                    "duplicate_emails": duplicate_emails,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_user_ids = []
        for student in all_students:
            user, created = User.objects.get_or_create(
                email=student["email"],
                defaults={
                    "first_name": student["first_name"],
                    "last_name": student["last_name"],
                    "role": "student",
                    "is_active": False,
                },
            )
            if created:
                user.activation_token = uuid.uuid4()
                user.save()
                new_user_ids.append(user.pk)

            school = School.objects.get(pk=school_id)
            grade = int(student["grade"])
            section = student["section"]
            school_class, created = Class.objects.get_or_create(
                school=school,
                grade=grade,
                section=section,
            )
            Student.objects.get_or_create(
                user=user,
                school_class=school_class,
                school=school,
                grade=grade,
            )

        if new_user_ids:
            send_mass_activation_email.delay(new_user_ids)

        return Response(
            {
                "message": "Excel file processed successfully",
                "num_students": len(all_students),
                "students": all_students,
            },
            status=status.HTTP_200_OK,
        )
