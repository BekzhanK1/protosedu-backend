from rest_framework import generics, permissions
from account.permissions import IsAuthenticated, HasSubscription, IsSuperUser
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import ChatSession, ChatMessage
from .serializers import ChatSessionSerializer, ChatMessageSerializer
from django.shortcuts import get_object_or_404
from .tasks import generate_openai_answer
from django.db import transaction


class ChatSessionListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated, HasSubscription | IsSuperUser]

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChatSessionDeleteView(generics.DestroyAPIView):
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated, HasSubscription | IsSuperUser]

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        # Optionally, you can handle any cleanup here
        instance.delete()


class ChatMessageListView(generics.ListAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated, HasSubscription | IsSuperUser]

    def get_queryset(self):
        chat_id = self.kwargs["chat_id"]
        return ChatMessage.objects.filter(
            chat__id=chat_id, chat__user=self.request.user
        )


class ChatMessageCreateView(APIView):
    permission_classes = [IsAuthenticated, HasSubscription | IsSuperUser]

    def post(self, request, chat_id):
        chat = get_object_or_404(ChatSession, id=chat_id, user=request.user)
        content = request.data.get("content", "").strip()

        if not content:
            return Response({"error": "Message content is required"}, status=400)

        # Create user message immediately and trigger async generation
        try:
            with transaction.atomic():
                if chat.title == "New chat":
                    chat.title = content[:50] + ("..." if len(content) > 50 else "")
                    chat.save()

                user_msg = ChatMessage.objects.create(
                    chat=chat, role="user", content=content
                )

            # Send task to generate AI response
            generate_openai_answer.delay(
                chat.subject, content, chat.id, request.user.id, user_msg.id
            )

            return Response(
                {
                    "message": "Message sent successfully",
                    "user_message_id": user_msg.id,
                },
                status=201,
            )

        except Exception as e:
            return Response({"error": "Failed to save message"}, status=500)
