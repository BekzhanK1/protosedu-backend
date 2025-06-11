from django.urls import path
from ai_tutor.consumers import GeminiConsumer

websocket_urlpatterns = [
    path("ws/chat/<int:chat_id>/", GeminiConsumer.as_asgi()),
]
