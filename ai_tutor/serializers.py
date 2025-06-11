from rest_framework import serializers
from .models import ChatSession, ChatMessage


class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = ["id", "title", "subject", "created_at"]  # add 'user' if needed

    # Optional: If you want to include messages inside the session
    # messages = ChatMessageSerializer(many=True, read_only=True)


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "chat", "role", "content", "created_at"]
        read_only_fields = ["created_at"]
