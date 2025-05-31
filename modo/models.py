from django.db import models
from django.db.models import Q, UniqueConstraint

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
    text = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to="answer_options/images/", blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    option_type = models.CharField(max_length=5, choices=CONTENT_TYPE, default="text")

    def __str__(self):
        return f"{self.text[:30] if self.text else 'Image Option'} - {'Correct' if self.is_correct else 'Incorrect'}"


class TestAnswer(models.Model):
    question = models.ForeignKey(
        Question, related_name="test_answers", on_delete=models.CASCADE
    )
    answer_option = models.ForeignKey(
        AnswerOption, related_name="test_answers", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        "account.User",
        related_name="test_answers",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    child = models.ForeignKey(
        "account.Child",
        related_name="test_answers",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        user_or_child = (
            f"User: {self.user.id}" if self.user else f"Child: {self.child.id}"
        )
        return f"{user_or_child} - {self.question.title} - Score: {self.is_correct}"

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["question", "user"],
                condition=Q(user__isnull=False),
                name="unique_user_question",
            ),
            UniqueConstraint(
                fields=["question", "child"],
                condition=Q(child__isnull=False),
                name="unique_child_question",
            ),
        ]


class TestResult(models.Model):
    test = models.ForeignKey(Test, related_name="results", on_delete=models.CASCADE)
    user = models.ForeignKey(
        "account.User",
        related_name="test_results",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    child = models.ForeignKey(
        "account.Child",
        related_name="test_results",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    is_finished = models.BooleanField(default=False)
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    date_taken = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("test", "user", "child")
        ordering = ["-date_taken"]

    def __str__(self):
        user_or_child = (
            f"User: {self.user.id}" if self.user else f"Child: {self.child.id}"
        )
        return f"{user_or_child} - {self.test.title} - Score: {self.score}"
