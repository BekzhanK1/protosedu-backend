from django.db import models

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
    test_type = models.CharField(max_length=4, choices=TEST_TYPE, default="modo")

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
