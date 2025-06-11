from django.contrib import admin

from .models import ChatSession, ChatMessage


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "subject", "created_at")
    search_fields = ("title", "user__username")
    list_filter = ("subject", "created_at")
    ordering = ("-created_at",)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "chat", "role", "created_at")
    search_fields = ("chat__title", "content")
    list_filter = ("role", "created_at")
    ordering = ("-created_at",)
