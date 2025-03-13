from django.db.models.signals import post_delete, post_save
from django.core.cache import cache
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from account.models import Child, Parent, Student
from subscription.models import Subscription
from tasks.models import Chapter, Course, Section


User = get_user_model()


@receiver(post_delete, sender=Student)
def delete_user_with_student(sender, instance, **kwargs):
    """Deletes the related User when a Student is deleted."""
    if instance.user:
        instance.user.delete()


def invalidate_user_cache(user_id):
    """Deletes cached user data when relevant models are updated."""
    cache_key = f"user_data_{user_id}"
    cache.delete(cache_key)


# Invalidate cache when User data changes
@receiver(post_save, sender=User)
@receiver(post_delete, sender=User)
def clear_user_cache(sender, instance, **kwargs):
    invalidate_user_cache(instance.id)


@receiver(post_save, sender=Subscription)
@receiver(post_delete, sender=Subscription)
def clear_subscription_cache(sender, instance, **kwargs):
    invalidate_user_cache(instance.user.id)


@receiver(post_save, sender=Student)
@receiver(post_delete, sender=Student)
def clear_student_cache(sender, instance, **kwargs):
    invalidate_user_cache(instance.user.id)


@receiver(post_save, sender=Parent)
@receiver(post_delete, sender=Parent)
def clear_parent_cache(sender, instance, **kwargs):
    invalidate_user_cache(instance.user.id)


@receiver(post_save, sender=Child)
@receiver(post_delete, sender=Child)
def clear_child_cache(sender, instance, **kwargs):
    invalidate_user_cache(instance.parent.user.id)


def invalidate_child_cache(child_id):
    """Deletes cached child data when the model is updated or deleted."""
    cache_key = f"child_data_{child_id}"
    cache.delete(cache_key)


@receiver(post_save, sender=Child)
@receiver(post_delete, sender=Child)
def clear_child_cache(sender, instance, **kwargs):
    invalidate_child_cache(instance.pk)


@receiver(post_save, sender=Course)
@receiver(post_delete, sender=Course)
def invalidate_courses_cache(sender, instance, **kwargs):
    """Clears the course list cache when a course is added, updated, or deleted."""
    print("Invalidating courses cache...")

    cache_keys = [
        "courses_all",
        f"courses_{instance.grade}_{instance.language}",
    ]

    for key in cache_keys:
        cache.delete(key)

    print("Cache invalidated:", cache_keys)


@receiver(post_save, sender=Section)
@receiver(post_delete, sender=Section)
def invalidate_course_cache_on_section_change(sender, instance, **kwargs):
    """Clears the cached course when a section is added, updated, or deleted."""
    print(f"Invalidating course cache due to section change: {instance.course.id}")
    if instance.course:
        cache_key = f"course_{instance.course.id}"
        cache.delete(cache_key)
        print("Cache invalidated:", cache_key)


@receiver(post_save, sender=Section)
@receiver(post_delete, sender=Section)
def invalidate_sections_cache(sender, instance, **kwargs):
    """Clears the cached section when a section is added, updated, or deleted."""
    if instance.course:
        cache_key = f"sections_{instance.course.id}"
        cache.delete(cache_key)
        print("Cache invalidated:", cache_key)


@receiver(post_save, sender=Chapter)
@receiver(post_delete, sender=Chapter)
def invalidate_section_cache_on_chapter_change(sender, instance, **kwargs):
    """Clears the cached chapters when a chapter is added, updated, or deleted."""
    if instance.section:
        cache_key = f"section_{instance.section.id}"
        cache.delete(cache_key)
        print("Cache invalidated:", cache_key)
