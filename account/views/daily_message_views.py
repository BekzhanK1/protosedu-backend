from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from account.models import LANGUAGE_CHOICES, DailyMessage, MotivationalPhrase
from datetime import date

from account.permissions import IsSuperUser
from account.serializers import DailyMessageSerializer, MotivationalPhraseSerializer
from account.tasks import generate_daily_messages


class DailyMessageView(APIView):
    def patch(self, request):
        user = request.user
        if not user.is_superuser:
            return Response(
                {"error": "You do not have permission to perform this action."},
                status=403,
            )
        languages = request.data.get("languages")
        if not languages:
            generate_daily_messages.delay()
            return Response(
                {"message": "Daily messages generation started."}, status=200
            )
        if not isinstance(languages, list):
            return Response({"error": "Languages should be a list."}, status=400)
        for language in languages:
            if language not in [choice[0] for choice in LANGUAGE_CHOICES]:
                return Response({"error": f"Invalid language: {language}."}, status=400)
        generate_daily_messages.delay(languages)
        return Response({"message": "Daily messages generation started."}, status=200)

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


class DailyMessageViewSet(viewsets.ModelViewSet):
    serializer_class = DailyMessageSerializer
    permission_classes = [IsSuperUser]
    queryset = DailyMessage.objects.all()
    cache_timeout = 0

    def get_queryset(self):
        language = self.request.query_params.get("language")
        if language:
            return self.queryset.filter(language=language)
        return self.queryset.filter(date=date.today())

    def list(self, request, *args, **kwargs):
        print("DailyMessageViewSet list method called")
        return super().list(request, *args, **kwargs)

    @action(
        detail=False,
        methods=["patch"],
        url_path="set-daily-message",
        permission_classes=[IsSuperUser],
    )
    def set_daily_message(self, request):
        print("set_daily_message method called")
        phrase_id = request.query_params.get("phrase")
        if not phrase_id:
            return Response({"error": "Phrase ID is required."}, status=400)

        if not phrase_id.isdigit():
            return Response({"error": "Phrase ID must be a number."}, status=400)

        phrase_id = int(phrase_id)

        if phrase_id < 1:
            return Response({"error": "Phrase ID must be greater than 0."}, status=400)

        phrase = get_object_or_404(MotivationalPhrase, id=phrase_id)

        daily_message, created = DailyMessage.objects.update_or_create(
            language=phrase.language,
            date=date.today(),
            defaults={"message": phrase.text, "is_active": True},
        )

        if created:
            print("Daily message created")
        else:
            print("Daily message updated")
        return Response(
            {
                "message": "Daily message set successfully.",
                "daily_message": DailyMessageSerializer(daily_message).data,
            },
            status=200,
        )


class MotivationalPhraseViewSet(viewsets.ModelViewSet):
    serializer_class = MotivationalPhraseSerializer
    queryset = MotivationalPhrase.objects.all()
    permission_classes = [IsSuperUser]

    def get_queryset(self):
        language = self.request.query_params.get("language")
        if language:
            return self.queryset.filter(language=language)
        return self.queryset
