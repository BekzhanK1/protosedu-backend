from django.db import models
from django.contrib.auth import get_user_model

# from account.models import Child

User = get_user_model()

SUBJECT_CHOICES = (
    ("math", "Math"),
    ("biology", "Biology"),
    ("physics", "Physics"),
    ("chemistry", "Chemistry"),
    ("history", "History"),
    ("geography", "Geography"),
    ("computer_science", "Computer Science"),
    ("art", "Art"),
    ("music", "Music"),
    ("kazakh", "Kazakh Language"),
    ("russian", "Russian Language"),
    ("english", "English Language"),
)


class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chats")
    title = models.CharField(max_length=255, default="New Chat")
    created_at = models.DateTimeField(auto_now_add=True)
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES, default="math")

    def __str__(self):
        return f"Chat #{self.id} ({self.title})"


class ChatMessage(models.Model):
    ROLE_CHOICES = (
        ("user", "User"),
        ("assistant", "Assistant"),
    )

    chat = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role.capitalize()} @ {self.created_at:%Y-%m-%d %H:%M}"
