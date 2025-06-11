import os
from django.db import transaction
from django.db.models.signals import post_save
from datetime import datetime

from django.http import FileResponse
import pandas as pd
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from account.tasks import decrement_schoolclass_grade, increment_schoolclass_grade

from account.models import Class, School, Student, User
from account.permissions import IsSuperUser
from account.serializers import SchoolSerializer, SupervisorRegistrationSerializer
from subscription.models import Plan, Subscription
from account.signals import (
    clear_user_cache,
    clear_student_cache,
    clear_subscription_cache,
)

from ..tasks import send_mass_activation_email, send_user_credentials_to_admins
from ..utils import cyrillic_to_username

from django.conf import settings
from django.contrib.auth.hashers import make_password


DEFAULT_PASSWORD = settings.STUDENT_DEFAULT_PASSWORD
DEFAULT_EMAIL = settings.STUDENT_DEFAULT_EMAIL


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

    @action(
        detail=True,
        methods=["patch"],
        url_path="increment-grade",
        url_name="increment-grade",
    )
    def increment_grade(self, request, pk=None):
        school = self.get_object()
        classes = school.classes.all()

        if not classes:
            return Response(
                {"message": "No classes found for this school"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            for school_class in classes:
                increment_schoolclass_grade.delay(school_class.id)

            return Response(
                {"message": "Grades incremented successfully"},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"message": f"Error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=True,
        methods=["patch"],
        url_path="decrement-grade",
        url_name="decrement-grade",
    )
    def decrement_grade(self, request, pk=None):
        school = self.get_object()
        classes = school.classes.all()

        if not classes:
            return Response(
                {"message": "No classes found for this school"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            for school_class in classes:
                decrement_schoolclass_grade.delay(school_class.id)

            return Response(
                {"message": "Grades decremented successfully"},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"message": f"Error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=False,
        methods=["patch"],
        url_path="increment-grades-global",
        url_name="increment-grades-global",
        permission_classes=[IsSuperUser],
    )
    def increment_grades_global(self, request):
        for school in School.objects.all():
            classes = school.classes.all()
            if not classes:
                continue

            try:
                for school_class in classes:
                    increment_schoolclass_grade.delay(school_class.id)
            except Exception as e:
                return Response(
                    {"message": f"Error occurred: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        return Response(
            {"message": "All school grades incremented successfully"},
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["patch"],
        url_path="decrement-grades-global",
        url_name="decrement-grades-global",
        permission_classes=[IsSuperUser],
    )
    def decrement_grades_global(self, request):
        for school in School.objects.all():
            classes = school.classes.all()
            if not classes:
                continue

            try:
                for school_class in classes:
                    decrement_schoolclass_grade.delay(school_class.id)
            except Exception as e:
                return Response(
                    {"message": f"Error occurred: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        return Response(
            {"message": "All school grades decremented successfully"},
            status=status.HTTP_200_OK,
        )

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

        try:
            with transaction.atomic():
                school.supervisor.delete()
                school.supervisor = None
                school.save()

            return Response(
                {"message": "Supervisor has been removed from the school"},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"message": f"Error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
        subscriptionPlan = request.data.get("plan", None)
        if not subscriptionPlan:
            return Response(
                {"message": "Plan is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        school_id = request.query_params.get("school_id")
        if not file:
            return Response(
                {"message": "No file was uploaded"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not school_id:
            return Response(
                {"message": "School ID is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return self.parse_excel(file, school_id, subscriptionPlan)

    def parse_excel(self, file, school_id, subcriptionPlan):
        """
        Parses the uploaded Excel file, extracts student data,
        and checks for duplicate emails before processing further.
        """
        try:
            xls = pd.ExcelFile(file)
        except Exception as e:
            print("1", e)
            return Response(
                {"message": f"Invalid Excel file format: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        names_to_drop = ["Оқушының аты-жөні"]
        all_students = []

        def generate_unique_username(first_name, last_name):
            base = cyrillic_to_username(f"{first_name} {last_name}")
            username = base
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base}{counter}"
                counter += 1
            return username

        def load_clean_sheet(sheet_name):
            try:
                df = pd.read_excel(xls, sheet_name=sheet_name, skiprows=1)

                df.columns = [
                    "№",
                    "Оқушының аты-жөні",
                    "Параллель",
                    "Литер",
                    "Ата-анасының электронды почтасы",
                ]
                df[["Жөні", "Аты"]] = df["Оқушының аты-жөні"].str.split(
                    n=2, expand=True
                )[[0, 1]]
                df = df.drop(columns=["№"])
                df = df.dropna(subset=["Оқушының аты-жөні"])
                df = df.dropna(subset=["Параллель"])
                df = df.dropna(subset=["Литер"])
                df = df.dropna(subset=["Ата-анасының электронды почтасы"])
                df = df[~df["Оқушының аты-жөні"].isin(names_to_drop)]
                df = df.drop(columns=["Оқушының аты-жөні"])

                students = [
                    {
                        "first_name": (
                            row["Аты"].strip()
                            if pd.notna(row["Аты"]) and row["Аты"].strip()
                            else None
                        ),
                        "last_name": (
                            row["Жөні"].strip()
                            if pd.notna(row["Жөні"]) and row["Жөні"].strip()
                            else None
                        ),
                        "grade": (
                            row["Параллель"] if pd.notna(row["Параллель"]) else None
                        ),
                        "section": (
                            row["Литер"].strip()
                            if pd.notna(row["Литер"]) and row["Литер"].strip()
                            else None
                        ),
                        "email": (
                            row["Ата-анасының электронды почтасы"].strip()
                            if pd.notna(row["Ата-анасының электронды почтасы"])
                            and row["Ата-анасының электронды почтасы"].strip()
                            else None
                        ),
                    }
                    for _, row in df.iterrows()
                ]

            except Exception as e:
                print("2", e)
                return Response(
                    {"message": f"Error processing sheet '{sheet_name}': {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            print("length", len(students))

            return students

        for sheet in xls.sheet_names:
            try:
                sheet_students = load_clean_sheet(sheet)
                all_students.extend(sheet_students)
            except Exception as e:
                print("3", e)
                return Response(
                    {"message": f"Error processing sheet '{sheet}': {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        new_user_ids = []
        user_credentials = []

        try:
            hashed_password = make_password(DEFAULT_PASSWORD)
            disconnect_signals()
            with transaction.atomic():
                school = School.objects.get(pk=school_id)

                exceptions = []
                for student in all_students:
                    email = (student.get("email") or "").strip()
                    first_name = (student.get("first_name") or "").strip()
                    last_name = (student.get("last_name") or "").strip()
                    grade = student.get("grade")
                    section = (student.get("section") or "").strip()
                    print(
                        "Processing student:",
                        first_name,
                        last_name,
                        grade,
                        section,
                        email,
                    )

                    if not first_name:
                        exceptions.append(
                            f"Student with email '{email}' and class '{grade}{section}' has no first name"
                        )
                    if not last_name:
                        exceptions.append(
                            f"Student with email '{email}' and class '{grade}{section}' has no last name"
                        )
                    if not grade or not section:
                        exceptions.append(
                            f"Student with email '{email}' has missing grade or section"
                        )
                    if not email or "@" not in email:
                        exceptions.append(
                            f"Student '{first_name} {last_name}' has an invalid or missing email"
                        )
                        # Optionally set default email:
                        # student["email"] = DEFAULT_EMAIL

                if exceptions:
                    return Response(
                        {
                            "message": "Error processing students",
                            "number_of_students": len(all_students),
                            "exceptions": exceptions,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                for student in all_students:
                    username = generate_unique_username(
                        student["first_name"],
                        student["last_name"],
                    )
                    user, created = User.objects.get_or_create(
                        username=username,
                        email=student["email"] if student["email"] != "" else None,
                        defaults={
                            "first_name": student["first_name"],
                            "last_name": student["last_name"],
                            "role": "student",
                            "is_active": True,
                            "requires_password_change": True,
                        },
                    )
                    if created:
                        plan, _ = Plan.objects.get_or_create(duration=subcriptionPlan)
                        Subscription.objects.create(user=user, plan=plan)
                        user.password = hashed_password
                        user.save()
                        new_user_ids.append(user.pk)
                        user_credentials.append(
                            {
                                "Фамилия": user.last_name,
                                "Имя": user.first_name,
                                "Имя пользователя": user.username,
                                "Пароль": DEFAULT_PASSWORD,
                                "Email": user.email,
                                "Класс": f"{student['grade']}{student['section']}",
                            }
                        )

                    else:
                        user_credentials.append(
                            {
                                "Фамилия": user.last_name,
                                "Имя": user.first_name,
                                "Имя пользователя": user.username,
                                "Пароль": "Already exists",
                                "Email": user.email,
                                "Класс": f"{student['grade']}{student['section']}",
                            }
                        )

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

            reconnect_signals()
            if user_credentials:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
                filename = f"credentials_{school.name}-{school.city}_{timestamp}.xlsx"
                df = pd.DataFrame(user_credentials)
                df = df.sort_values(by="Фамилия")

                credentials_dir = os.path.join(
                    settings.MEDIA_ROOT, "school-credentials"
                )
                os.makedirs(credentials_dir, exist_ok=True)

                credentials_file = os.path.join(credentials_dir, filename)
                df.to_excel(credentials_file, index=False)
                send_user_credentials_to_admins.delay(credentials_file, school.name)

            # if new_user_ids:
            #     send_mass_activation_email.delay(new_user_ids)

            return Response(
                {
                    "message": "Excel file processed successfully",
                    "num_students": len(all_students),
                    "students": all_students,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            print("4", e)
            return Response(
                {"message": f"Error processing students: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=False,
        methods=["get"],
        url_path="list-credentials",
        permission_classes=[IsSuperUser],
    )
    def list_credentials(self, request):
        dir_path = os.path.join(settings.MEDIA_ROOT, "school-credentials")
        if not os.path.exists(dir_path):
            return Response({"files": []}, status=status.HTTP_200_OK)

        files = []
        for filename in sorted(os.listdir(dir_path), reverse=True):
            if filename.endswith(".xlsx"):

                def human_readable_size(size):
                    for unit in ["B", "KB", "MB", "GB", "TB"]:
                        if size < 1024:
                            return f"{size:.2f} {unit}"
                        size /= 1024
                    return f"{size:.2f} PB"

                files.append(
                    {
                        "name": filename,
                        "url": request.build_absolute_uri(
                            f"/media/school-credentials/{filename}"
                        ),
                        "created_at": datetime.fromtimestamp(
                            os.path.getmtime(os.path.join(dir_path, filename))
                        ).strftime("%Y-%m-%d %H:%M:%S"),
                        "size": human_readable_size(
                            os.path.getsize(os.path.join(dir_path, filename))
                        ),
                    }
                )

        return Response({"files": files}, status=status.HTTP_200_OK)

    from django.http import FileResponse

    @action(
        detail=False,
        methods=["get"],
        url_path="download-credential",
        permission_classes=[IsSuperUser],
    )
    def download_credential(self, request):
        filename = request.query_params.get("filename")
        if not filename:
            return Response({"message": "Filename is required"}, status=400)

        # Prevent path traversal attacks
        if ".." in filename or "/" in filename or "\\" in filename:
            return Response({"message": "Invalid filename"}, status=400)

        file_path = os.path.join(settings.MEDIA_ROOT, "school-credentials", filename)
        if not os.path.exists(file_path):
            return Response({"message": "File not found"}, status=404)

        return FileResponse(
            open(file_path, "rb"),
            as_attachment=True,
            filename=filename,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    @action(
        detail=False,
        methods=["delete"],
        url_path="delete-credential",
        permission_classes=[IsSuperUser],
    )
    def delete_credential(self, request):
        filename = request.query_params.get("filename")
        if not filename:
            return Response({"message": "Filename is required"}, status=400)

        if ".." in filename or "/" in filename or "\\" in filename:
            return Response({"message": "Invalid filename"}, status=400)

        path = os.path.join(settings.MEDIA_ROOT, "school-credentials", filename)
        if not os.path.exists(path):
            return Response({"message": "File not found"}, status=404)

        try:
            os.remove(path)
            return Response({"message": "File deleted successfully"}, status=204)
        except Exception as e:
            return Response(
                {"message": f"Error deleting file: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=True,
        methods=["delete"],
        url_path="delete-school",
        permission_classes=[IsSuperUser],
    )
    def delete_school(self, request, pk=None):
        """
        Deletes a school and all associated data.
        """
        school = self.get_object()
        try:
            disconnect_signals()
            with transaction.atomic():
                for school_class in school.classes.all():
                    for student in school_class.students.all():
                        student.user.delete()
                    school_class.delete()
                if school.supervisor:
                    school.supervisor.delete()
                school.delete()
            reconnect_signals()
            return Response(
                {"message": "School deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Exception as e:
            return Response(
                {"message": f"Error deleting school: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


def disconnect_signals():
    """
    Disconnects signals to prevent cache clearing during bulk operations.
    This is useful when creating or updating multiple objects at once.
    """
    post_save.disconnect(clear_user_cache, sender=User)
    post_save.disconnect(clear_student_cache, sender=Student)
    post_save.disconnect(clear_subscription_cache, sender=Subscription)


def reconnect_signals():
    """
    Reconnects signals after bulk operations are done.
    This is useful to restore the normal behavior of cache clearing.
    """
    post_save.connect(clear_user_cache, sender=User)
    post_save.connect(clear_student_cache, sender=Student)
    post_save.connect(clear_subscription_cache, sender=Subscription)
