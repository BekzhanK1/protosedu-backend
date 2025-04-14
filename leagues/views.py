from django.shortcuts import render
from django.db import transaction
from django.db.models import Prefetch, Count
from rest_framework.views import APIView
from rest_framework.response import Response
import math
from random import shuffle

from account.models import Child, School, Student
from leagues.models import League, LeagueGroup, LeagueGroupParticipant


class TestingView(APIView):
    def get(self, request):
        try:
            with transaction.atomic():
                # Example of League creation
                league = League.objects.create(
                    name="Test League",
                    rank=1,
                    description="A test league for demonstration purposes.",
                    max_players=50,
                    promotions_rate=10,
                    demotions_rate=5,
                )

                # Create LeagueGroupParticipants for each student and child
                for student in Student.objects.all():
                    LeagueGroupParticipant.objects.create(
                        student=student,
                        cups_earned=0,
                    )

                for child in Child.objects.all():
                    LeagueGroupParticipant.objects.create(
                        child=child,
                        cups_earned=0,
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
