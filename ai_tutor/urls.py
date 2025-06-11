from django.urls import path
from .views import (
    ChatSessionDeleteView,
    ChatSessionListCreateView,
    ChatMessageListView,
    ChatMessageCreateView,
)

urlpatterns = [
    path("sessions/", ChatSessionListCreateView.as_view(), name="chat-list-create"),
    path("sessions/<int:pk>/", ChatSessionDeleteView.as_view(), name="chat-delete"),
    path(
        "sessions/<int:chat_id>/messages/",
        ChatMessageListView.as_view(),
        name="chat-messages",
    ),
    path(
        "sessions/<int:chat_id>/send/",
        ChatMessageCreateView.as_view(),
        name="chat-send",
    ),
]
