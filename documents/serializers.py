from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Document, Subject
import os


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "id",
            "file",
            "name",
            "subject",
            "language",
            "order",
            "document_type",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "name": {
                "error_messages": {
                    "required": _("Name is required."),
                    "blank": _("Name cannot be blank."),
                }
            },
            "file": {
                "error_messages": {
                    "required": _("File is required."),
                    "blank": _("File cannot be blank."),
                }
            },
            "document_type": {
                "error_messages": {
                    "required": _("Document type is required."),
                    "blank": _("Document type cannot be blank."),
                }
            },
            "subject": {
                "error_messages": {
                    "required": _("Subject is required."),
                    "blank": _("Subject cannot be blank."),
                }
            },
        }
        read_only_fields = ["created_at", "updated_at"]


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name", "description", "grade", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]
        extra_kwargs = {
            "name": {
                "error_messages": {
                    "required": _("Name is required."),
                    "blank": _("Name cannot be blank."),
                }
            },
            "description": {
                "error_messages": {
                    "required": _("Description is required."),
                    "blank": _("Description cannot be blank."),
                }
            },
            "grade": {
                "error_messages": {
                    "required": _("Grade is required."),
                    "blank": _("Grade cannot be blank."),
                }
            },
        }
