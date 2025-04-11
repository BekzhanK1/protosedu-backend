from django.db import models

from account.models import GRADE_CHOICES
from django.db import transaction

DOCUMENT_TYPES = (("ktp", "KTP"),)


class Subject(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    grade = models.IntegerField(
        choices=GRADE_CHOICES,
        default=1,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name or "Unnamed Subject"


class Document(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    file = models.FileField(upload_to="documents/")
    order = models.IntegerField(default=0, null=False)
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    document_type = models.CharField(
        max_length=64,
        choices=DOCUMENT_TYPES,
        default="ktp",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if not self.pk:
                last_order = (
                    Document.objects.filter(subject=self.subject)
                    .order_by("-order")
                    .first()
                )
                self.order = last_order.order + 1 if last_order else 1
            super().save(*args, **kwargs)

    def __str__(self):
        return self.name or "Unnamed Document"
