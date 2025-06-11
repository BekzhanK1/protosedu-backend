from django.db.models.signals import post_delete, post_save, pre_delete
from django.core.cache import cache
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from account.models import Child, DailyMessage, Parent, Student
from account.tasks import (
    course_invalidate_cache,
    invalidate_user_cache,
    delete_keys_matching,
)
from subscription.models import Subscription
from tasks.models import Chapter, Content, Course, Lesson, Section, Task, TaskCompletion


User = get_user_model()


# @receiver(post_delete, sender=Student)
# def delete_user_with_student(sender, instance, **kwargs):
#     """Deletes the related User when a Student is deleted."""
#     if instance.user:
#         instance.user.delete()


# Invalidate cache when User data changes
@receiver(post_save, sender=User)
@receiver(post_delete, sender=User)
def clear_user_cache(sender, instance, **kwargs):
    invalidate_user_cache.delay(instance.id)
    patterns = [
        f"courses_user_{instance.id}*",
        f"course_user_{instance.id}*",
    ]
    for pattern in patterns:
        delete_keys_matching.delay(pattern=pattern)


@receiver(post_save, sender=Subscription)
@receiver(pre_delete, sender=Subscription)
def clear_subscription_cache(sender, instance, **kwargs):
    if instance.user:
        invalidate_user_cache.delay(instance.user.id)


@receiver(post_save, sender=Student)
@receiver(pre_delete, sender=Student)
def clear_student_cache(sender, instance, **kwargs):
    if instance.user:
        invalidate_user_cache.delay(instance.user.id)


@receiver(post_save, sender=Parent)
@receiver(pre_delete, sender=Parent)
def clear_parent_cache(sender, instance, **kwargs):
    if instance.user:
        invalidate_user_cache.delay(instance.user.id)


def invalidate_child_cache(child_id):
    """Deletes cached child data when the model is updated or deleted."""
    cache_key = f"child_data_{child_id}"
    cache.delete(cache_key)


@receiver(post_save, sender=Child)
@receiver(pre_delete, sender=Child)
def clear_child_cache(sender, instance, **kwargs):
    invalidate_user_cache.delay(instance.parent.user.id)
    invalidate_child_cache(instance.pk)


@receiver([post_save, post_delete], sender=Course)
def invalidate_courses_cache(sender, instance, **kwargs):
    try:
        print(f"Invalidating cache for course {instance.pk}")
        delete_keys_matching.delay()
    except Exception as e:
        print(f"Exception in invalidate_courses_cache: {e}")


@receiver([post_save, post_delete], sender=Section)
def invalidate_sections_cache(sender, instance, **kwargs):
    delete_keys_matching.delay()
    delete_keys_matching.delay(pattern="section*")


@receiver([post_save, post_delete], sender=Chapter)
def invalidate_chapters_cache(sender, instance, **kwargs):
    delete_keys_matching.delay(pattern="section*")
    delete_keys_matching.delay(pattern="chapter*")


@receiver([post_save, post_delete], sender=Task)
def invalidate_tasks_cache(sender, instance, **kwargs):
    delete_keys_matching.delay(pattern="content*")
    delete_keys_matching.delay(pattern="chapter*")
    delete_keys_matching.delay(pattern="section*")
    delete_keys_matching.delay(pattern="task*")


@receiver([post_save, post_delete], sender=Lesson)
def invalidate_lessons_cache(sender, instance, **kwargs):
    delete_keys_matching.delay(pattern="content*")
    delete_keys_matching.delay(pattern="chapter*")
    delete_keys_matching.delay(pattern="section*")
    delete_keys_matching.delay(pattern="lesson*")


@receiver([post_save, pre_delete], sender=TaskCompletion)
def invalidate_task_completion_cache(sender, instance, **kwargs):
    task = instance.task
    chapter = task.chapter
    section = chapter.section
    course = section.course

    if not course:
        return

    user_id = None

    try:
        if instance.user:
            user_id = instance.user.id
    except Exception as e:
        print(f"[Signal] Error resolving user/child in TaskCompletion: {e}")
        # Optionally skip invalidation if critical data is missing
        return

    patterns = [
        f"courses_user_{user_id}*",
        f"course_user_{user_id}*",
        f"sections_user_{user_id}*",
        f"section_user_{user_id}*",
        f"chapters_user_{user_id}*",
        f"chapter_user_{user_id}*",
        f"tasks_user_{user_id}*",
        f"task_user_{user_id}*",
        f"lessons_user_{user_id}*",
        f"lesson_user_{user_id}*",
        f"content_user_{user_id}*",
        f"contents_user_{user_id}*",
    ]

    for pattern in patterns:
        print(f"Invalidating cache for pattern: {pattern}")
        delete_keys_matching.delay(pattern=pattern)


@receiver([post_save, post_delete], sender=DailyMessage)
def invalidate_daily_message_cache(sender, instance, **kwargs):
    cache_key = f"daily_message_{instance.language}"
    print(f"Invalidating cache for {cache_key}")
    cache.delete(cache_key)
