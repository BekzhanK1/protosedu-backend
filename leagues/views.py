from django.shortcuts import render
from django.db import transaction
from django.core.cache import cache
from django.db.models import Prefetch, Count
from rest_framework.views import APIView
from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
import math
from random import shuffle, randint

from account.models import Child, School, Student
from account.permissions import IsSuperUser, IsAuthenticated
from .models import League, LeagueGroup, LeagueGroupParticipant
from .serializers import (
    LeagueSerializer,
    LeagueGroupSerializer,
    LeagueGroupParticipantSerializer,
)
from .utils import (
    get_league_cache_key,
    get_league_list_cache_key,
    get_league_group_cache_key,
    get_league_group_list_cache_key,
    get_league_group_participant_list_cache_key,
)

from .league_utils import end_league_week


class LeagueViewSet(viewsets.ModelViewSet):
    serializer_class = LeagueSerializer

    def get_queryset(self):
        queryset = League.objects.all()
        queryset = queryset.annotate(number_of_groups=Count("student_groups"))
        rank = self.request.query_params.get("rank")
        if rank:
            queryset = queryset.filter(rank=rank)
        return queryset

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            self.permission_classes = [IsSuperUser]
        else:
            self.permission_classes = [IsAuthenticated]

        return [permission() for permission in self.permission_classes]

    def list(self, request, *args, **kwargs):
        cache_key = get_league_list_cache_key()
        cached_data = cache.get(cache_key)

        if cached_data:
            print("Cache hit", cached_data)
            return Response(cached_data)

        print("Cache miss")

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=3600)
        return response

    def retrieve(self, request, *args, **kwargs):
        cache_key = get_league_cache_key(kwargs["pk"])
        cached_data = cache.get(cache_key)
        if cached_data:
            print("Cache hit", cached_data)
            return Response(cached_data)

        print("Cache miss")

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=3600)
        return response


class LeagueGroupViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    serializer_class = LeagueGroupSerializer

    def get_queryset(self):
        queryset = LeagueGroup.objects.all()
        league_id = self.request.query_params.get("league_id")

        if league_id:
            queryset = queryset.filter(league_id=league_id)
            print(f"Applying filter for league_id: {league_id}")

        queryset = queryset.select_related("league")
        return queryset

    def get_permissions(self):
        self.permission_classes = [IsAuthenticated]
        return [permission() for permission in self.permission_classes]

    def list(self, request, *args, **kwargs):
        league_id = self.request.query_params.get("league_id")
        cache_key = get_league_group_list_cache_key(league_id)
        cached_data = cache.get(cache_key)

        if cached_data:
            print("Cache hit")
            return Response(cached_data)

        print("Cache miss")

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=3600)
        return response

    def retrieve(self, request, *args, **kwargs):
        cache_key = get_league_group_cache_key(kwargs["pk"])
        cached_data = cache.get(cache_key)
        if cached_data:
            print("Cache hit")
            return Response(cached_data)

        print("Cache miss")

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=3600)
        return response

    @action(detail=True, methods=["get"])
    def standings(self, request, pk=None):
        """
        Get participants for a specific league group.
        """
        cache_key = get_league_group_participant_list_cache_key(pk)
        cached_data = cache.get(cache_key)
        if cached_data:
            print("Cache hit")
            return Response(cached_data)

        print("Cache miss")
        participant_prefetch = Prefetch(
            "participants",
            queryset=LeagueGroupParticipant.objects.order_by(
                "-cups_earned",
                "last_question_answered",
            ).select_related("student", "child"),
            to_attr="prefetched_participants",
        )
        league_group = (
            LeagueGroup.objects.select_related("league")
            .prefetch_related(participant_prefetch)
            .get(pk=pk)
        )
        participants = league_group.prefetched_participants
        response_data = {}
        participant_data = [
            {
                "place": index + 1,
                "student": str(participant.student) if participant.student else None,
                "child": str(participant.child) if participant.child else None,
                "cups_earned": participant.cups_earned,
                "rank": participant.rank,
                "last_question_answered": participant.last_question_answered,
            }
            for index, participant in enumerate(participants)
        ]
        league_data = {
            "league_name": league_group.league.name,
            "group_name": league_group.group_name,
            "max_players": league_group.league.max_players,
            "promotions_rate": league_group.league.promotions_rate,
            "demotions_rate": league_group.league.demotions_rate,
            "participants_number": len(participants),
        }
        response_data["league"] = league_data
        response_data["participants"] = participant_data

        cache.set(cache_key, response_data, timeout=600)
        return Response(response_data)


class TestingView(APIView):

    def post(self, request):
        leagues = League.objects.all()
        for league in leagues:
            end_league_week(league)
        return Response({"message": "League weeks ended successfully."})

    def patch(self, request):
        league_group_id = request.query_params.get("group")
        if not league_group_id:
            return Response({"error": "No league_id is specified"})

        league_group = LeagueGroup.objects.prefetch_related("participants").get(
            pk=league_group_id
        )

        participants = league_group.participants

        try:
            with transaction.atomic():
                for participant in participants:
                    participant.cups = randint(0, 10000)
                    participant.save()

            return Response({"message": "Succesfully randomized"})

        except Exception as e:
            return Response({"error": f"Exception: {e}"})

    def get(self, request):
        try:
            with transaction.atomic():
                # Example of League creation
                league = League.objects.create(
                    name="Test League",
                    rank=1,
                    description="A test league for demonstration purposes.",
                    max_players=25,
                    promotions_rate=10,
                    demotions_rate=5,
                )

                # Create LeagueGroupParticipants for each student and child
                for student in Student.objects.all():
                    LeagueGroupParticipant.objects.create(
                        rank=league.rank,
                        student=student,
                        cups_earned=randint(0, 10000),
                    )

                for child in Child.objects.all():
                    LeagueGroupParticipant.objects.create(
                        rank=league.rank,
                        child=child,
                        cups_earned=randint(0, 10000),
                    )

                # Get the total number of participants (students + children)
                number_of_participants = LeagueGroupParticipant.objects.all().count()
                print(f"Number of participants: {number_of_participants}")

                # Calculate the number of groups (rounding up)
                number_of_groups = math.ceil(
                    number_of_participants / league.max_players
                )
                print(f"Number of groups: {number_of_groups}")

                # Create League Groups
                for i in range(number_of_groups):
                    LeagueGroup.objects.create(
                        league=league,
                        group_name=f"Group {i + 1}",
                    )

                # Get all participants and shuffle them
                participants = list(LeagueGroupParticipant.objects.all())
                shuffle(participants)

                # Get the created groups
                groups = list(LeagueGroup.objects.filter(league=league))

                # Distribute participants to groups
                for index, participant in enumerate(participants):
                    group = groups[
                        index % len(groups)
                    ]  # Round-robin assignment to groups
                    participant.league_group = group
                    participant.save()
            return Response(
                {
                    "message": "League groups created and participants assigned successfully."
                }
            )
        except Exception as e:
            print(f"An error occurred: {e}")
            return Response({"error": str(e)}, status=500)


class CheckLeagueView(APIView):
    def get(self, request):
        # Prefetch participants for groups, with select_related for student and child
        participant_prefetch = Prefetch(
            "participants",
            queryset=LeagueGroupParticipant.objects.select_related("student", "child"),
            to_attr="prefetched_participants",
        )

        # Prefetch groups, annotate with participant count, and prefetch participants
        groups_prefetch = Prefetch(
            "student_groups",
            queryset=LeagueGroup.objects.annotate(
                participants_number=Count("participants")
            ).prefetch_related(participant_prefetch),
            to_attr="prefetched_groups",
        )

        # Prefetch everything at once
        leagues = League.objects.prefetch_related(groups_prefetch).all()

        response_data = []

        for league in leagues:
            league_data = {
                "league_name": league.name,
                "rank": league.rank,
                "number_of_groups": len(league.prefetched_groups),
                "groups": [],
            }

            for group in league.prefetched_groups:
                group_data = {
                    "group_name": group.group_name,
                    "participants_number": group.participants_number,
                    "participants": [
                        {
                            "student": (
                                str(participant.student)
                                if participant.student
                                else None
                            ),
                            "child": (
                                str(participant.child) if participant.child else None
                            ),
                            "cups_earned": participant.cups_earned,
                        }
                        for participant in getattr(group, "prefetched_participants", [])
                    ],
                }

                league_data["groups"].append(group_data)

            response_data.append(league_data)

        return Response(response_data)
