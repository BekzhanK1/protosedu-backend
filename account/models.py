from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

GRADE_CHOICES = [(i, str(i)) for i in range(-1, 12)]  # -1 means for everyone
SECTION_CHOICES = (
    [(chr(i), chr(i)) for i in range(ord("A"), ord("Z") + 1)]
    + [(chr(i), chr(i)) for i in range(ord("А"), ord("Я") + 1)]
    + [(chr(i), chr(i)) for i in range(ord("Ә"), ord("Ө") + 1)]
    + [(chr(i), chr(i)) for i in range(ord("Ү"), ord("Я") + 1)]
)
GENDER_CHOICES = [
    ("M", "Male"),
    ("F", "Female"),
    ("O", "Other"),
]
LANGUAGE_CHOICES = [
    ("ru", "Russian"),
    ("kz", "Kazakh"),
    ("en", "English"),
    ("cm", "Common"),
]


class CustomUserManager(BaseUserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError("The Username field must be set")

        email = self.normalize_email(email) if email else None  # Ensure it's nullable
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            username=username, email=email, password=password, **extra_fields
        )


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ("student", "Student"),
        ("parent", "Parent"),
        ("teacher", "Teacher"),
        ("supervisor", "Supervisor"),
    )
    username = models.CharField(max_length=150, blank=True, null=True, unique=True)
    email = models.EmailField(db_index=True, blank=True, null=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=150)
    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{1,4}?[\s\-\(\)]*\d{1,4}?[\s\-\(\)]*\d{1,4}?[\s\-\(\)]*\d{1,4}?[\s\-\(\)]*\d{1,9}$",
        message="Phone number must be entered in the format: '+7 (705) 723 8447'. Up to 15 digits allowed.",
    )
    phone_number = models.CharField(
        validators=[phone_regex], max_length=17, blank=True, null=True
    )
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    requires_password_change = models.BooleanField(default=False)
    activation_token = models.UUIDField(editable=False, null=True, blank=True)
    activation_token_expires_at = models.DateTimeField(null=True, blank=True)
    reset_password_token = models.UUIDField(editable=False, null=True, blank=True)
    reset_password_token_expires_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    @property
    def is_student(self):
        return self.role == "student"

    @property
    def is_parent(self):
        return self.role == "parent"

    @property
    def is_teacher(self):
        return self.role == "teacher"

    @property
    def is_supervisor(self):
        return self.role == "supervisor"

    @property
    def is_activation_token_expired(self):
        return (
            self.activation_token_expires_at < timezone.now()
            if self.activation_token_expires_at
            else True
        )

    @property
    def is_reset_password_token_expired(self):
        return (
            self.reset_password_token_expires_at < timezone.now()
            if self.reset_password_token_expires_at
            else True
        )

    def get_short_name(self):
        return self.first_name

    def get_full_name(self):
        """Return the full name for the user."""
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"


class School(models.Model):
    name = models.CharField(max_length=150)
    city = models.CharField(max_length=150)
    email = models.EmailField(unique=False)
    supervisor = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="school"
    )

    def __str__(self):
        return f"{self.name} ({self.city})"


class Class(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="classes")
    grade = models.IntegerField(choices=GRADE_CHOICES)
    section = models.CharField(max_length=1, choices=SECTION_CHOICES)
    language = models.CharField(max_length=50, choices=LANGUAGE_CHOICES, default="kz")

    def __str__(self):
        return f"{self.grade}{self.section}"


class LevelRequirement(models.Model):
    level = models.PositiveIntegerField(unique=True)
    cups_required = models.PositiveIntegerField()

    def __str__(self):
        return f"Level {self.level}: {self.cups_required} cups"


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student")
    school_class = models.ForeignKey(
        Class, on_delete=models.SET_NULL, null=True, blank=True, related_name="students"
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="students",
    )
    grade = models.IntegerField(choices=GRADE_CHOICES)
    level = models.PositiveIntegerField(default=1)
    streak = models.PositiveIntegerField(default=0)
    cups = models.PositiveIntegerField(default=0)
    stars = models.PositiveIntegerField(default=0)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default="O")
    language = models.CharField(max_length=50, choices=LANGUAGE_CHOICES, default="kz")
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    birth_date = models.DateField(default=date(2015, 1, 1), blank=True, null=True)
    last_task_completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"[Student: {self.pk}] {self.user.first_name} {self.user.last_name}"

    def update_level(self):
        for requirement in LevelRequirement.objects.order_by("level"):
            if self.cups >= requirement.cups_required:
                self.level = requirement.level
            else:
                break
        self.save()

    def update_streak(self):
        now = timezone.now()
        if self.last_task_completed_at:
            if now.date() == self.last_task_completed_at.date():
                return
            elif now.date() == (self.last_task_completed_at + timedelta(days=1)).date():
                self.streak += 1
            else:
                self.streak = 1
        else:
            self.streak = 1
        self.last_task_completed_at = now
        self.save()

    def add_question_reward(self):
        question_reward = settings.QUESTION_REWARD
        self.cups += question_reward
        self.stars += question_reward
        self.save()


class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="parent")

    def __str__(self):
        return f"[Parent] {self.user.first_name} {self.user.last_name}"


class Child(models.Model):
    parent = models.ForeignKey(
        Parent, on_delete=models.CASCADE, related_name="children"
    )
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=150)
    grade = models.IntegerField(choices=GRADE_CHOICES)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default="O")
    language = models.CharField(max_length=50, choices=LANGUAGE_CHOICES, default="ru")
    cups = models.PositiveIntegerField(default=0)
    stars = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    streak = models.PositiveIntegerField(default=0)
    birth_date = models.DateField(default=date(2015, 1, 1))
    last_task_completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"[Child: {self.pk}] {self.first_name} {self.last_name}"

    def update_level(self):
        for requirement in LevelRequirement.objects.order_by("level"):
            if self.cups >= requirement.cups_required:
                self.level = requirement.level
            else:
                break
        self.save()

    def update_streak(self):
        now = timezone.now()
        if self.last_task_completed_at:
            if now.date() == self.last_task_completed_at.date():
                return
            elif now.date() == (self.last_task_completed_at + timedelta(days=1)).date():
                self.streak += 1
            else:
                self.streak = 1
        else:
            self.streak = 1
        self.last_task_completed_at = now
        self.save()

    def add_question_reward(self):
        question_reward = settings.QUESTION_REWARD
        self.cups += question_reward
        self.stars += question_reward
        self.save()


class MotivationalPhrase(models.Model):
    text = models.CharField(max_length=255)
    language = models.CharField(max_length=50, choices=LANGUAGE_CHOICES, default="ru")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.text


class DailyMessage(models.Model):
    message = models.TextField()
    language = models.CharField(max_length=50, choices=LANGUAGE_CHOICES, default="ru")
    is_active = models.BooleanField(default=True)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.date} {self.message}"
