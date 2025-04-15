from jsonschema import ValidationError
from .models import League, LeagueGroup, LeagueGroupParticipant
from django.db import transaction


def end_league_week_for_group(league_group):
    """
    Process the league group for ending the league week, promoting and demoting participants.
    """
    promotions_rate = league_group.league.promotions_rate
    demotions_rate = league_group.league.demotions_rate

    # Get all participants in the league group, ordered by cups earned and last answered time
    league_group_participants = LeagueGroupParticipant.objects.filter(
        league_group=league_group
    ).order_by(
        "-cups_earned",
        "last_question_answered",
    )

    total_participants = len(league_group_participants)

    if total_participants < promotions_rate + demotions_rate:
        return

    # Separate participants for promotion and demotion
    participants_to_promote = []
    participants_to_demote = []
    unchanged_participants = []

    for participant in league_group_participants:
        if participant.cups_earned > 0:
            if len(participants_to_promote) < promotions_rate:
                participants_to_promote.append(participant)
            else:
                participants_to_demote.append(participant)
        else:
            participants_to_demote.append(participant)

    # Edge case handling for promotions
    if len(participants_to_promote) < promotions_rate:
        remaining_spots = promotions_rate - len(participants_to_promote)
        participants_to_promote += participants_to_demote[:remaining_spots]
        participants_to_demote = participants_to_demote[remaining_spots:]

    # Ensure there are no more participants than required
    participants_to_promote = participants_to_promote[:promotions_rate]
    participants_to_demote = participants_to_demote[:demotions_rate]

    # Identify unchanged participants
    for participant in league_group_participants:
        if (
            participant not in participants_to_promote
            and participant not in participants_to_demote
        ):
            unchanged_participants.append(participant)

    # Tie-breaking logic
    tie_break_promotions(participants_to_promote)
    tie_break_demotions(participants_to_demote)

    # Use atomic transactions to ensure consistency
    try:
        with transaction.atomic():
            for participant in participants_to_promote:
                # participant.rank = league_group.league.rank + 1
                participant.rank = participant.rank + 1
                participant.save()
                print(f"Promoting participant {participant} to rank {participant.rank}")
                send_promotion_feedback(participant)

            for participant in participants_to_demote:
                if league_group.league.rank > 0:
                    # participant.rank = league_group.league.rank - 1
                    participant.rank = participant.rank - 1
                    participant.save()
                    print(
                        f"Demoting participant {participant} to rank {participant.rank}"
                    )
                    send_demotion_feedback(participant)

            for participant in league_group_participants:
                participant.cups_earned = 0
                participant.save()

    except ValidationError as e:
        print(f"Error while ending the league week for group {league_group}: {e}")

    # Log unchanged participants for clarity
    print(f"Unchanged participants for {league_group}:")
    for participant in unchanged_participants:
        print(f"- {participant}")


def tie_break_promotions(participants):
    """
    Resolve tie-breaks for promotions.
    If multiple participants have the same XP and last_answered, prioritize based on the most recent activity.
    """
    if len(participants) > 1:
        # Sorting by cups earned and then by last answered time
        participants.sort(
            key=lambda x: (x.cups_earned, x.last_question_answered), reverse=True
        )


def tie_break_demotions(participants):
    """
    Resolve tie-breaks for demotions.
    Similar to promotions, but for the bottom ranks.
    """
    if len(participants) > 1:
        # Sorting by cups earned and then by last answered time
        participants.sort(
            key=lambda x: (x.cups_earned, x.last_question_answered), reverse=False
        )


def send_promotion_feedback(participant):
    """
    Send feedback to the participant about their promotion.
    """
    # Implement the logic to send feedback
    print(f"Sending promotion feedback to {participant}")


def send_demotion_feedback(participant):
    """
    Send feedback to the participant about their demotion.
    """
    # Implement the logic to send feedback
    print(f"Sending demotion feedback to {participant}")
