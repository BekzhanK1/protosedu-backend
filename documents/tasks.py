from typing import List
from celery import shared_task
from django.core.cache import cache


@shared_task
def invalidate_cache_celery(cache_keys: List[str]):
    for cache_key in cache_keys:
        print(cache_key)
    cache.delete_many(cache_keys)
