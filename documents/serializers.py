from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Document
import os


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "id",
            "file",
            "name",
            "document_type",
            "grade",
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
            "grade": {
                "error_messages": {
                    "required": _("Grade is required."),
                    "blank": _("Grade cannot be blank."),
                }
            },
        }
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        file = validated_data.get("file")
        filename = os.path.basename(file.name)  # Get the file name from the path

        if not validated_data.get("name"):
            validated_data["name"] = filename

        return super().create(validated_data)

    def update(self, instance, validated_data):
        file = validated_data.get("file", instance.file)
        filename = os.path.basename(file.name)  # Get the file name from the path

        if not validated_data.get("name"):
            validated_data["name"] = filename

        return super().update(instance, validated_data)
