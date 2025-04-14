from celery import shared_task, group


@shared_task
def process_league_ending(league_id):
    """
    Celery task to process a single league.
    """
    from .models import League
    from .league_utils import end_league_week

    league = League.objects.get(id=league_id)
    end_league_week(league)


@shared_task
def celery_end_league_week():
    """
    Celery task to end the league week by delegating work to workers.
    This will run all tasks concurrently using Celery's `group`.
    """
    from .models import League

    leagues = League.objects.all()

    # Create a group of tasks for each league
    tasks = group(process_league_ending.s(league.id) for league in leagues)

    # Execute the tasks concurrently
    tasks.apply_async()
