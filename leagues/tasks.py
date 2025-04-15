from celery import shared_task

from leagues.league_utils import end_league_week_for_group


@shared_task
def process_league_group(league_group_id):
    """
    Celery task to process a single league group.
    """
    from .models import LeagueGroup

    league_group = LeagueGroup.objects.get(id=league_group_id)

    end_league_week_for_group(league_group)


@shared_task
def celery_end_league_week():
    """
    Celery task to end the league week by delegating work to workers for each league group.
    """
    from .models import LeagueGroup

    league_groups = LeagueGroup.objects.all()

    for league_group in league_groups:
        process_league_group.delay(league_group.id)
