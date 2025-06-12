import concurrent
from .models import ChatSession, ChatMessage
from .openai_model import get_tutor_model
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from celery import shared_task


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
def generate_openai_answer(subject, question, chat_id, user_id, user_message_id):
    print("Generating answer for subject:", subject)
    print("Question:", question)

    try:
        chat = ChatSession.objects.get(id=chat_id, user__id=user_id)
    except ChatSession.DoesNotExist:
        print("Chat session not found")
        return "⚠️ Sorry, I couldn't find the chat session. Please try again later."

    # Get latest messages and format them for OpenAI
    latest_messages = ChatMessage.objects.filter(chat=chat).order_by("-created_at")[:10]
    formatted_messages = [
        {"role": msg.role, "content": msg.content} for msg in latest_messages
    ]
    # Add the new user question at the end
    formatted_messages.append({"role": "user", "content": question})

    print("Formatted messages:", formatted_messages)

    try:
        model_fn = get_tutor_model(subject, formatted_messages)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(model_fn)
            answer = future.result(timeout=15)
            print(f"Generated answer: {answer}")

    except concurrent.futures.TimeoutError:
        print("LLM timeout error")
        answer = "⚠️ Sorry, I couldn't generate an answer due to a timeout. Please try again later."
    except Exception as e:
        print("LLM error:", e)
        answer = "⚠️ Sorry, I couldn't generate an answer due to an internal error."

    # Save assistant message and push to frontend
    try:
        assistant_msg = ChatMessage.objects.create(
            chat=chat, role="assistant", content=answer
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{chat.id}",
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

    except Exception as e:
        print("DB/WebSocket error:", e)
        return "✅ Answer generated, but failed to deliver it to chat UI."
