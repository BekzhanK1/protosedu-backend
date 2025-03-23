from django.contrib.auth import get_user_model
from django.db import models

from account.models import GRADE_CHOICES, LANGUAGE_CHOICES, Child

User = get_user_model()


COURSE_TYPES = [
    ("regular", "Regular"),
    # ("modo", "MODO"),
    # ("ent", "ENT"),
]


class Course(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    course_type = models.CharField(
        max_length=50, choices=COURSE_TYPES, default="regular"
    )
    grade = models.IntegerField(choices=GRADE_CHOICES)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    language = models.CharField(max_length=50, choices=LANGUAGE_CHOICES, default="ru")

    class Meta:
        ordering = ["grade"]

    def __str__(self):
        return f"{self.name} ({self.grade} Класс)"


class Section(models.Model):
    course = models.ForeignKey(
        Course, related_name="sections", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def save(self, *args, **kwargs):
        if self.order == 0:
            last_order = Section.objects.filter(course=self.course).aggregate(
                models.Max("order")
            )["order__max"]
            self.order = (last_order + 1) if last_order is not None else 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Chapter(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)
    section = models.ForeignKey(
        Section, related_name="chapters", null=True, on_delete=models.CASCADE
    )

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.section.title} - {self.title}"


class Content(models.Model):
    CONTENT_TYPE_CHOICES = (
        ("task", "Task"),
        ("lesson", "Lesson"),
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)
    chapter = models.ForeignKey(
        Chapter, related_name="contents", null=True, on_delete=models.CASCADE
    )
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES)
    video_url = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ["order"]

    def save(self, *args, **kwargs):
        if self.order == 0:
            last_order = Content.objects.filter(chapter=self.chapter).aggregate(
                models.Max("order")
            )["order__max"]
            self.order = (last_order + 1) if last_order is not None else 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Content: (Chapter: {self.chapter} | Order: {self.order})"


class Lesson(Content):
    def __str__(self):
        return f"Lesson: {self.title}"


class Task(Content):
    def __str__(self):
        return f"Task: {self.title}"


class Question(models.Model):
    QUESTION_TYPES = [
        ("multiple_choice_text", "Multiple Choice Text"),
        ("multiple_choice_images", "Multiple Choice Images"),
        ("drag_and_drop_text", "Drag and Drop Text"),
        ("drag_and_drop_images", "Drag and Drop Images"),
        ("true_false", "True or False"),
        ("mark_all", "Mark All That Apply"),
        ("number_line", "Number Line"),
        ("drag_position", "Drag Position"),
        ("click_image", "Click Image"),
        ("input_text", "Input Text")
    ]
    task = models.ForeignKey(Task, related_name="questions", on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    question_text = models.TextField()
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPES)
    options = models.JSONField(blank=True, null=True)
    correct_answer = models.JSONField()
    template = models.CharField(default="1", max_length=20, blank=True, null=True)
    audio = models.FileField(upload_to="audio/", blank=True, null=True)
    content = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"[Task: {self.task}] {self.question_text}"


class Image(models.Model):
    option_id = models.PositiveIntegerField(default=0, blank=True, null=True)
    image = models.ImageField(upload_to="questions/")
    question = models.ForeignKey(
        Question, related_name="images", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"Image for {self.question.id}"


class Answer(models.Model):
    user = models.ForeignKey(
        User, null=True, blank=True, related_name="answers", on_delete=models.CASCADE
    )
    child = models.ForeignKey(
        Child, null=True, blank=True, related_name="answers", on_delete=models.CASCADE
    )
    question = models.ForeignKey(
        Question, related_name="answers", on_delete=models.CASCADE
    )
    # answer = models.TextField()
    is_correct = models.BooleanField()

    class Meta:
        unique_together = (("user", "question"), ("child", "question"))

    def __str__(self):
        return f"{self.user} - {self.question}"


class TaskCompletion(models.Model):
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        related_name="completed_tasks",
        on_delete=models.CASCADE,
    )
    child = models.ForeignKey(
        Child,
        null=True,
        blank=True,
        related_name="completed_tasks",
        on_delete=models.CASCADE,
    )
    task = models.ForeignKey(
        Task, related_name="completed_by", on_delete=models.CASCADE
    )
    correct = models.PositiveSmallIntegerField(default=0)
    wrong = models.PositiveSmallIntegerField(default=0)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("user", "task"), ("child", "task"))

    def __str__(self):
        return f"{self.user or self.child} - {self.task}"
