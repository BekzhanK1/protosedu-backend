from django.db.models.signals import post_delete, post_save
from django.core.cache import cache
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from account.models import Child, Parent, Student
from subscription.models import Subscription


User = get_user_model()


@receiver(post_delete, sender=Student)
def delete_user_with_student(sender, instance, **kwargs):
    """Deletes the related User when a Student is deleted."""
    if instance.user:
        instance.user.delete()


def invalidate_user_cache(user_id):
    """Deletes cached user data when relevant models are updated."""
    print("Invalidating cache for user", user_id)
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
