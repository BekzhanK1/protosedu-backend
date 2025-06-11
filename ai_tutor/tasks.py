from .models import ChatSession, ChatMessage
from .gemini_model import get_tutor_model
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from celery import shared_task


@shared_task
def generate_gemini_answer(subject, question, chat_id, user_id, user_message_id):
    print("Generating answer for subject:", subject)
    print("Question:", question)
    model = get_tutor_model(subject)
    response = model.generate_content(question)
    answer = response.text
    print(f"Generated answer: {answer}")

    # Save assistant response in DB
    chat = ChatSession.objects.get(id=chat_id, user__id=user_id)
    assistant_msg = ChatMessage.objects.create(
        chat=chat, role="assistant", content=answer
    )

    # Send via WebSocket to frontend
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"chat_{chat.id}",  # Group name
        {
            "type": "chat.message",
            "message": {
                "id": assistant_msg.id,
                "role": assistant_msg.role,
                "content": assistant_msg.content,
                "created_at": assistant_msg.created_at.isoformat(),
                "in_response_to": user_message_id,
            },
        },
    )

    return answer
