from django.db import models

from account.models import GRADE_CHOICES

DOCUMENT_TYPES = (("ktp", "KTP"),)


class Document(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    file = models.FileField(upload_to="documents/")
    document_type = models.CharField(
        max_length=64,
        choices=DOCUMENT_TYPES,
        default="ktp",
    )
    grade = models.IntegerField(choices=GRADE_CHOICES, default=-1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
