from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from documents.tasks import invalidate_cache_celery
from django.core.cache import cache
from .models import LeagueGroup, LeagueGroupParticipant, League
from .utils import (
    get_league_cache_key,
    get_league_list_cache_key,
    get_league_group_list_cache_key,
    get_league_group_cache_key,
    get_league_group_participant_list_cache_key,
)


@receiver([post_save, post_delete], sender=League)
def invalidate_cache_leagues(sender, instance, **kwargs):
    cache_keys = [get_league_cache_key(instance.pk), get_league_list_cache_key()]
    print(f"Invalidating cache for league: {instance.pk}")
    for league_group in instance.student_groups.all():
        cache_keys.append(get_league_group_participant_list_cache_key(league_group.pk))
    invalidate_cache_celery.delay(cache_keys)


@receiver([post_save, post_delete], sender=LeagueGroup)
def invalidate_cache_league_groups(sender, instance, **kwargs):
    cache_keys = [
        get_league_group_cache_key(instance.pk),
        get_league_group_list_cache_key(),
        get_league_group_list_cache_key(instance.league_id),
        get_league_group_participant_list_cache_key(instance.pk),
    ]
    print(f"Invalidating cache for league group: {instance.pk}")
    invalidate_cache_celery.delay(cache_keys)


@receiver([post_save, post_delete], sender=LeagueGroupParticipant)
def invalidate_cache_league_group_participants(sender, instance, **kwargs):
    cache_key = get_league_group_participant_list_cache_key(instance.league_group_id)
    if cache.get(cache_key):
        print(f"Invalidating cache for league group participant: {instance.pk}")
        invalidate_cache_celery.delay([cache_key])
    else:
        print(
            f"No cache found for league group participant: {instance.pk}, skipping invalidation."
        )
