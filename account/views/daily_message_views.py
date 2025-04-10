from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.cache import cache
from account.models import LANGUAGE_CHOICES, DailyMessage
from datetime import date


class DailyMessageView(APIView):
    def get(self, request):
        language = request.query_params.get("language")
        if language is None:
            return Response({"error": "Language is required."}, status=400)

        if language not in [choice[0] for choice in LANGUAGE_CHOICES]:
            return Response({"error": "Invalid language."}, status=400)

        if cache.get(f"daily_message_{language}"):
            # Cache hit
            print("Cache hit")

            return Response(
                {
                    "message": cache.get(f"daily_message_{language}"),
                    "language": language,
                },
                status=200,
            )

        # Cache miss
        print("Cache miss")

        try:
            daily_message = DailyMessage.objects.get(
                language=language, is_active=True, date=date.today()
            )
            cache.set(f"daily_message_{language}", daily_message.message, timeout=3600)
            return Response(
                {"message": daily_message.message, "language": language}, status=200
            )
        except DailyMessage.DoesNotExist:
            return Response(
                {"message": "No message found for the specified language."}, status=404
            )
