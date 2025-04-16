from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from documents.tasks import invalidate_cache_celery
from .utils import get_complaint_list_cache_key, get_complaint_cache_key

from .models import Complaint


@receiver([post_save, post_delete], sender=Complaint)
def invalidate_cache_complaints(sender, instance, **kwargs):
    """
    Invalidate cache for complaint list and specific complaint.
    """
    cache_keys = [get_complaint_list_cache_key(), get_complaint_cache_key(instance.pk)]
    print("Cache keys to invalidate:", cache_keys)
    invalidate_cache_celery.delay(cache_keys)
