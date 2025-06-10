from celery import shared_task
from .gemini_model import get_tutor_model


@shared_task
def generate_gemini_answer(subject, question):
    model = get_tutor_model(subject)
    response = model.generate_content(question)
    print(f"Generated response for question: {question}")
    print(f"Response: {response.text}")
    return response.text
