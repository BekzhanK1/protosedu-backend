from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Document, DOCUMENT_TYPES, Subject
from account.models import GRADE_CHOICES
from .tasks import invalidate_cache_celery


@receiver([post_save, post_delete], sender=Subject)
def invalidate_cache_subjects(sender, instance, **kwargs):
    cache_keys = [f"subject_{instance.pk}", "subjects_list_grade_None"]
    for grade, _ in GRADE_CHOICES:
        cache_keys.append(f"subjects_list_grade_{grade}")
    print(cache_keys)
    invalidate_cache_celery.delay(cache_keys)


@receiver([post_save, post_delete], sender=Document)
def invalidate_cache_documents(sender, instance, **kwargs):
    cache_keys = [
        f"document_{instance.pk}",
    ]
    if instance.language:
        cache_keys.append(
            f"documents_list_subject_{instance.subject_id}_type_{instance.document_type}_language_{instance.language}"
        )
    else:
        cache_keys.append(
            f"documents_list_subject_{instance.subject_id}_type_{instance.document_type}"
        )

    for doc_type, _ in DOCUMENT_TYPES:
        if instance.language:
            cache_keys.append(
                f"documents_list_subject_{instance.subject_id}_type_{doc_type}_language_{instance.language}"
            )
        else:
            cache_keys.append(
                f"documents_list_subject_{instance.subject_id}_type_{doc_type}"
            )

    print(cache_keys)
    invalidate_cache_celery.delay(cache_keys)


@receiver(post_save, sender=Document)
def set_document_name(sender, instance, **kwargs):
    if not instance.name:
        instance.name = instance.file.name.split("/")[-1].split(".")[0]
        instance.save(update_fields=["name"])


@receiver(post_delete, sender=Document)
def delete_document_file(sender, instance, **kwargs):
    if instance.file:
        instance.file.delete(save=False)
