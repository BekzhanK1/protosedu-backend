import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .tasks import generate_gemini_answer


@csrf_exempt  # Only for testing; use proper auth for production!
def ask_question(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    try:
        data = json.loads(request.body)
        subject = data.get("subject")
        question = data.get("question")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not subject or not question:
        return JsonResponse({"error": "Subject and question are required."}, status=400)

    task = generate_gemini_answer.delay(subject, question)
    return JsonResponse({"task_id": task.id})
