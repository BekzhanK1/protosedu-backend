from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Document, DOCUMENT_TYPES
from account.models import GRADE_CHOICES
from .tasks import invalidate_cache_celery


@receiver([post_save, post_delete], sender=Document)
def invalidate_cache_documents(sender, instance, **kwargs):
    cache_keys = [
        f"document_{instance.pk}",
    ]
    for grade, _ in GRADE_CHOICES:
        for types, _ in DOCUMENT_TYPES:
            cache_keys.append(f"documents_list_grade_{grade}_type_{types}")
    cache_keys.append("documents_list_grade_None_type_None")
    print(cache_keys)
    invalidate_cache_celery.delay(cache_keys)
