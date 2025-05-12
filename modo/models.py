from django.db import models
from django.core.exceptions import ValidationError

TEST_TYPE = [
    ("modo", "MODO"),
    ("ent", "ENT"),
    ("diagnostic", "Diagnostic"),
    ("other", "Other"),
]

CONTENT_TYPE = [
    ("text", "Text"),
    ("image", "Image"),
]


class Test(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)
    test_type = models.CharField(max_length=20, choices=TEST_TYPE, default="modo")

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class Question(models.Model):
    test = models.ForeignKey(Test, related_name="questions", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class Content(models.Model):
    question = models.ForeignKey(
        Question, related_name="contents", on_delete=models.CASCADE
    )
    content_type = models.CharField(max_length=5, choices=CONTENT_TYPE, default="text")
    text = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="contents/images/", blank=True, null=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        if self.content_type == "text":
            return self.text[:30] if self.text else "Text Content"
        return "Image Content"


class AnswerOption(models.Model):
    question = models.ForeignKey(
        Question, related_name="answer_options", on_delete=models.CASCADE
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class TestAnswer(models.Model):
    child = models.ForeignKey(
        "account.Child",
        related_name="test_answers",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    user = models.ForeignKey(
        "account.User",
        related_name="test_answers",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    test = models.ForeignKey(Test, related_name="answers", on_delete=models.CASCADE)
    question = models.ForeignKey(
        Question, related_name="answers", on_delete=models.CASCADE
    )
    answer_option = models.ForeignKey(
        AnswerOption, related_name="answers", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_correct(self):
        return self.answer_option.is_correct

    class Meta:
        unique_together = (
            "child",
            "user",
            "test",
            "question",
            "answer_option",
        )
        ordering = ["-id"]
        verbose_name = "Test Answer"
        verbose_name_plural = "Test Answers"

    def __str__(self):
        return f"{self.child or self.user} - {self.test.title} - {self.question.title}"

    def clean(self):
        if not self.child and not self.user:
            raise ValidationError("Either 'child' or 'user' must be set.")
        if self.child and self.user:
            raise ValidationError("Only one of 'child' or 'user' can be set.")
