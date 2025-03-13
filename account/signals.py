from django.db.models.signals import post_delete, post_save
from django.core.cache import cache
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from account.models import Child, Parent, Student
from subscription.models import Subscription
from tasks.models import Chapter, Content, Course, Section


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
    """Clears course cache when a course is added, updated, or deleted."""
    print("Invalidating courses cache...")

    cache_keys = [
        f"courses_{grade}_{lang}"
        for grade in range(-1, 5)
        for lang in ["ru", "en", "kz"]
    ]
    cache_keys.append("courses_all")

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


@receiver([post_save, post_delete], sender=Section)
def invalidate_sections_cache(sender, instance, **kwargs):
    """Clears the cached sections and course when a section is modified."""
    if instance.course:
        course_cache_key = f"course_{instance.course.id}"
        sections_cache_key = f"sections_{instance.course.id}"
        cache.delete_many([course_cache_key, sections_cache_key])
        print("Cache invalidated:", course_cache_key, sections_cache_key)


@receiver(post_save, sender=Chapter)
@receiver(post_delete, sender=Chapter)
def invalidate_section_cache_on_chapter_change(sender, instance, **kwargs):
    """Clears the cached chapters when a chapter is added, updated, or deleted."""
    if instance.section:
        cache_key = f"section_{instance.section.id}"
        cache.delete(cache_key)
        cache.delete(f"sections_{instance.section.course.id}")
        print("Cache invalidated:", cache_key)


@receiver([post_save, post_delete], sender=Chapter)
def invalidate_chapter_cache(sender, instance, **kwargs):
    """Clears the cached chapter and related section when a chapter changes."""
    if instance.section:
        section_cache_key = f"section_{instance.section.id}"
        chapters_cache_key = f"chapters_{instance.section.id}"
        sections_cache_key = f"sections_{instance.section.course.id}"
        cache.delete_many([section_cache_key, chapters_cache_key, sections_cache_key])
        print("Cache invalidated:", section_cache_key, chapters_cache_key)


@receiver(post_save, sender=Content)
@receiver(post_delete, sender=Content)
def invalidate_task_cache(sender, instance, **kwargs):
    """Clears the cached chapter when a task is added, updated, or deleted."""
    if instance.chapter:
        chapter_cache_key = f"chapter_{instance.chapter.id}"
        chapters_cache_key = f"chapters_{instance.chapter.section.id}"
        section_cache_key = f"section_{instance.chapter.section.id}"
        cache.delete_many([chapter_cache_key, chapters_cache_key, section_cache_key])
        print(
            "Cache invalidated:",
            chapter_cache_key,
            chapters_cache_key,
            section_cache_key,
        )
