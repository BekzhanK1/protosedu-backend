import concurrent
from .models import ChatSession, ChatMessage
from .openai_model import get_tutor_model
from asgiref.sync import async_to_sync
# from channels.layers import get_channel_layer
from celery import shared_task
from django.db import transaction


# @shared_task
# def generate_gemini_answer(subject, question, chat_id, user_id, user_message_id):
#     print("Generating answer for subject:", subject)
#     print("Question:", question)
#     model = get_tutor_model(subject)
#     response = model.generate_content(question)
#     answer = response.text
#     print(f"Generated answer: {answer}")

#     # Save assistant response in DB
#     chat = ChatSession.objects.get(id=chat_id, user__id=user_id)
#     assistant_msg = ChatMessage.objects.create(
#         chat=chat, role="assistant", content=answer
#     )

#     # Send via WebSocket to frontend
#     channel_layer = get_channel_layer()
#     async_to_sync(channel_layer.group_send)(
#         f"chat_{chat.id}",  # Group name
#         {
#             "type": "chat.message",
#             "message": {
#                 "id": assistant_msg.id,
#                 "role": assistant_msg.role,
#                 "content": assistant_msg.content,
#                 "created_at": assistant_msg.created_at.isoformat(),
#                 "in_response_to": user_message_id,
#             },
#         },
#     )

#     return answer


@shared_task
def generate_openai_answer(subject, question, chat_id, user_id, user_msg_id):
    """Generate AI response with proper error handling"""

    print(f"🎓 Generating {subject} answer for chat {chat_id}")

    try:
        from .models import ChatSession, ChatMessage

        chat = ChatSession.objects.get(id=chat_id, user__id=user_id)
    except ChatSession.DoesNotExist:
        print("❌ Chat session not found")
        return

    try:
        # Get conversation history (excluding the current question)
        latest_messages = list(
            ChatMessage.objects.filter(chat=chat)
            .exclude(id=user_msg_id)  # Exclude the current user message
            .order_by("-created_at")[:10]
        )

        # Reverse to get chronological order
        latest_messages.reverse()

        # Format messages for AI
        formatted_messages = [
            {"role": msg.role, "content": msg.content} for msg in latest_messages
        ]

        # Add current question
        formatted_messages.append({"role": "user", "content": question})

        print(f"📝 Using {len(formatted_messages)} messages for context")

    except Exception as e:
        print(f"❌ Error preparing messages: {e}")
        formatted_messages = [{"role": "user", "content": question}]

    # Generate AI response
    try:
        model_fn = get_tutor_model(subject, formatted_messages)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(model_fn)
            answer = future.result(timeout=20)  # Increased timeout

        print(f"✅ Generated answer ({len(answer)} chars)")

    except concurrent.futures.TimeoutError:
        print("⏰ OpenAI timeout")
        answer = f"⚠️ I need more time to think about your {subject} question. Please try asking again!"

    except Exception as e:
        print(f"❌ AI generation error: {e}")
        answer = f"⚠️ I'm having trouble with your {subject} question right now. Could you try rephrasing it?"

    # Save AI response to database
    try:
        assistant_msg = ChatMessage.objects.create(
            chat=chat, role="assistant", content=answer
        )

        print(f"💾 Saved assistant message {assistant_msg.id}")

        # Send to WebSocket
        # channel_layer = get_channel_layer()
        # async_to_sync(channel_layer.group_send)(
        #     f"chat_{chat.id}",
        #     {
        #         "type": "chat.message",
        #         "message": {
        #             "id": assistant_msg.id,
        #             "role": assistant_msg.role,
        #             "content": assistant_msg.content,
        #             "created_at": assistant_msg.created_at.isoformat(),
        #             "in_response_to": user_msg_id,
        #         },
        #     },
        # )

        print(f"📡 Sent to WebSocket for chat {chat.id}")
        return answer

    except Exception as e:
        print(f"❌ Database/WebSocket error: {e}")
        # Try to send error message to frontend
        # try:
        #     channel_layer = get_channel_layer()
        #     async_to_sync(channel_layer.group_send)(
        #         f"chat_{chat.id}",
        #         {
        #             "type": "chat.error",
        #             "error": "Failed to save response. Please try again.",
        #             "in_response_to": user_msg_id,
        #         },
        #     )
        # except:
        #     pass

        return None
