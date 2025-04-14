from jsonschema import ValidationError
from .models import League, LeagueGroup, LeagueGroupParticipant
from django.db import transaction


def end_league_week(league: League):
    """
    Ends the current league week by resetting the cups and ranks of all participants.
    Only the top `promotion_rate` will be promoted, and the bottom `demotion_rate` will be demoted.
    Handles edge cases and tie-breaking logic. Participants not in promotion or demotion zones remain unchanged.
    """
    promotions_rate = league.promotions_rate
    demotions_rate = league.demotions_rate

    league_groups = LeagueGroup.objects.filter(league=league)

    for league_group in league_groups:
        # Get all participants in the league group, ordered by cups earned and last answered time
        league_group_participants = LeagueGroupParticipant.objects.filter(
            league_group=league_group
        ).order_by(
            "-cups_earned",
            "last_question_answered",
        )

        # Total number of participants in the group
        total_participants = len(league_group_participants)

        # Edge case: If there are not enough participants, skip this group
        if total_participants < promotions_rate + demotions_rate:
            continue

        # Separate participants for promotion and demotion
        participants_to_promote = []
        participants_to_demote = []
        unchanged_participants = []

        # First, prioritize participants with > 0 cups for promotion and those with 0 cups for demotion
        for participant in league_group_participants:
            if participant.cups_earned > 0:
                if len(participants_to_promote) < promotions_rate:
                    participants_to_promote.append(participant)
                else:
                    participants_to_demote.append(participant)
            else:
                participants_to_demote.append(participant)

        # Edge Case Handling: If we don't have enough participants with > 0 cups for promotion
        # Fill remaining promotions with those from the demotion zone if necessary
        if len(participants_to_promote) < promotions_rate:
            remaining_spots = promotions_rate - len(participants_to_promote)
            # Add the lowest ranked participants with 0 cups to the promotion zone if needed
            participants_to_promote += participants_to_demote[:remaining_spots]
            participants_to_demote = participants_to_demote[remaining_spots:]

        # Ensure that we don't have more than the required number of participants in the promotion zone
        participants_to_promote = participants_to_promote[:promotions_rate]
        participants_to_demote = participants_to_demote[:demotions_rate]

        # Identify unchanged participants (those who are neither promoted nor demoted)
        for participant in league_group_participants:
            if (
                participant not in participants_to_promote
                and participant not in participants_to_demote
            ):
                unchanged_participants.append(participant)

        # Handle tie-breaking logic for promotions and demotions
        tie_break_promotions(participants_to_promote)
        tie_break_demotions(participants_to_demote)

        # Use atomic transactions to ensure consistency
        try:
            with transaction.atomic():
                # Handle promotions and feedback
                for participant in participants_to_promote:
                    participant.rank = league.rank + 1
                    participant.save()
                    send_promotion_feedback(participant)

                # Handle demotions and feedback
                for participant in participants_to_demote:
                    if league.rank > 0:
                        participant.rank = league.rank - 1
                        participant.save()
                        send_demotion_feedback(participant)

                # Reset cups for the next week for all participants
                for participant in league_group_participants:
                    participant.cups_earned = 0
                    participant.save()

        except ValidationError as e:
            print(f"Error while ending the league week: {e}")

        # Display the unchanged participants for clarity
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
