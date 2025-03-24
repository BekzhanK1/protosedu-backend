from django.db.models.signals import post_delete, post_save
from django.core.cache import cache
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from account.models import Child, Parent, Student
from subscription.models import Subscription
from tasks.models import Chapter, Content, Course, Lesson, Section, Task, TaskCompletion


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
    try:
        course = instance.course
        if course:
            cache_key = f"course_{course.id}"
            cache.delete(cache_key)
            print("Cache invalidated:", cache_key)
    except Exception as e:
        print(f"[invalidate_course_cache_on_section_change] Skipped due to error: {e}")


@receiver([post_save, post_delete], sender=Section)
def invalidate_sections_cache(sender, instance, **kwargs):
    """Clears the cached sections and course when a section is modified."""
    try:
        course = instance.course
        if course:
            course_cache_key = f"course_{course.id}"
            sections_cache_key = f"sections_{course.id}"
            cache.delete_many([course_cache_key, sections_cache_key])
            print("Cache invalidated:", course_cache_key, sections_cache_key)
    except Exception as e:
        print(f"[invalidate_sections_cache] Skipped due to error: {e}")


@receiver(post_save, sender=Chapter)
@receiver(post_delete, sender=Chapter)
def invalidate_section_cache_on_chapter_change(sender, instance, **kwargs):
    """Clears the cached chapters when a chapter is added, updated, or deleted."""
    try:
        section = instance.section
        if section:
            section_key = f"section_{section.id}"
            course_key = f"sections_{section.course.id}" if section.course else None
            cache.delete(section_key)
            if course_key:
                cache.delete(course_key)
            print("Cache invalidated:", section_key, course_key)
    except Exception as e:
        print(f"[invalidate_section_cache_on_chapter_change] Skipped due to error: {e}")


@receiver([post_save, post_delete], sender=Chapter)
def invalidate_chapter_cache(sender, instance, **kwargs):
    """Clears the cached chapter and related section when a chapter changes."""
    try:
        section = instance.section
        if section:
            section_cache_key = f"section_{section.id}"
            chapters_cache_key = f"chapters_{section.id}"
            sections_cache_key = (
                f"sections_{section.course.id}" if section.course else None
            )

            cache_keys = [section_cache_key, chapters_cache_key]
            if sections_cache_key:
                cache_keys.append(sections_cache_key)

            cache.delete_many(cache_keys)
            print("Cache invalidated:", *cache_keys)
    except Exception as e:
        print(f"[invalidate_chapter_cache] Skipped due to error: {e}")


@receiver(post_save, sender=Task)
@receiver(post_delete, sender=Task)
def invalidate_task_cache_if_task(sender, instance, **kwargs):
    try:
        chapter = instance.chapter
        section = chapter.section
        course = section.course

        cache_keys = [
            f"chapter_{chapter.id}",
            f"chapters_{section.id}",
            f"section_{section.id}",
            f"sections_{course.id}",
        ]
        cache.delete_many(cache_keys)
        print("Cache invalidated:", *cache_keys)
    except Exception as e:
        print(f"[invalidate_task_cache_if_task] Skipped due to error: {e}")


@receiver(post_save, sender=Lesson)
@receiver(post_delete, sender=Lesson)
def invalidate_task_cache_if_lesson(sender, instance, **kwargs):
    try:
        chapter = instance.chapter
        section = chapter.section
        course = section.course

        cache_keys = [
            f"chapter_{chapter.id}",
            f"chapters_{section.id}",
            f"section_{section.id}",
            f"sections_{course.id}",
        ]
        cache.delete_many(cache_keys)
        print("Cache invalidated:", *cache_keys)
    except Exception as e:
        print(f"[invalidate_task_cache_if_lesson] Skipped due to error: {e}")


@receiver(post_save, sender=TaskCompletion)
def invalidate_task_cache_if_task_completion(sender, instance, **kwargs):
    try:
        task = instance.task
        chapter = task.chapter
        section = chapter.section
        course = section.course

        cache_keys = [
            f"chapter_{chapter.id}",
            f"chapters_{section.id}",
            f"section_{section.id}",
            f"sections_{course.id}",
        ]
        cache.delete_many(cache_keys)
        print("Cache invalidated:", *cache_keys)
    except Exception as e:
        print(f"[invalidate_task_cache_if_task_completion] Skipped due to error: {e}")
