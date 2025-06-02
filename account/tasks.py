from typing import List, Optional
import uuid
from datetime import timedelta
import random

from celery import group, shared_task
from django.conf import settings
from django.core.cache import cache
from account.utils import get_cache_key
from django.contrib.auth.hashers import make_password
from django.core.mail import (
    EmailMultiAlternatives,
    get_connection,
    send_mass_mail,
    EmailMessage,
)
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
import pandas as pd

from account.models import (
    Child,
    DailyMessage,
    MotivationalPhrase,
    Parent,
    Student,
    User,
    LANGUAGE_CHOICES,
)
from account.utils import generate_password, render_email
from subscription.models import Subscription
import logging

from tasks.models import Complaint

frontend_url = settings.FRONTEND_URL


print(f"CELERY TASKS ARE IN {settings.STAGE} MODE")


def send_mass_html_mail(datatuple, fail_silently=False):
    messages = []
    for subject, text_content, html_content, from_email, recipient_list in datatuple:
        msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
        msg.attach_alternative(html_content, "text/html")
        messages.append(msg)

    # try:
    #     # Try sending all messages in bulk
    #     connection = get_connection(fail_silently=fail_silently)
    #     connection.send_messages(messages)
    # except Exception as e:
    #     # If there is an issue, fallback to sending individually
    #     if not fail_silently:
    #         raise e
    #     for message in messages:
    #         try:
    #             message.send(fail_silently=fail_silently)
    #         except Exception as single_email_exception:
    #             if not fail_silently:
    #                 raise single_email_exception

    return len(messages)


@shared_task
def send_daily_email_to_all_students():
    students = Student.objects.all().select_related("user")
    datatuple = []
    # for student in students:
    #     if student.user.is_active:  # Ensure we only email active users
    #         html_content, text_content = render_email(
    #             student.user.first_name,
    #             student.user.last_name,
    #             student.cups,
    #             student.level,
    #             frontend_url + "/dashboard",
    #         )
    #         msg = (
    #             "Daily Update",
    #             text_content,
    #             html_content,
    #             settings.DEFAULT_FROM_EMAIL,
    #             [student.user.email],
    #         )
    #         datatuple.append(msg)

    # if datatuple:
    #     send_mass_html_mail(datatuple, fail_silently=False)


@shared_task
def send_daily_email_to_all_parents():
    parents = Parent.objects.all().select_related("user").prefetch_related("children")
    datatuple = []
    # for parent in parents:
    #     if (
    #         parent.user.is_active and parent.children.exists()
    #     ):  # Ensure the parent is active and has children
    #         context = {
    #             "first_name": parent.user.first_name,
    #             "last_name": parent.user.last_name,
    #             "children": parent.children.all(),
    #             "dashboard_url": frontend_url + "/dashboard",
    #         }
    #         html_content = render_to_string("parent_email_template.html", context)
    #         text_content = strip_tags(html_content)
    #         msg = (
    #             "Your Children’s Daily Update",
    #             text_content,
    #             html_content,
    #             settings.DEFAULT_FROM_EMAIL,
    #             [parent.user.email],
    #         )
    #         datatuple.append(msg)

    # if datatuple:
    #     send_mass_html_mail(datatuple, fail_silently=False)


BATCH_SIZE = 100


@shared_task
def send_mass_activation_email(user_ids):
    """Splits users into chunks and runs parallel tasks."""
    # chunks = [user_ids[i : i + BATCH_SIZE] for i in range(0, len(user_ids), BATCH_SIZE)]
    # task_group = group(send_activation_email_chunk.s(chunk) for chunk in chunks)
    # task_group.apply_async()
    # return f"Queued {len(chunks)} parallel tasks for {len(user_ids)} users."


@shared_task
def send_activation_email_chunk(user_ids):
    """Handles activation email sending for a batch of users."""
    logger = logging.getLogger("activation")
    users = User.objects.filter(id__in=user_ids)
    updated_users = []
    datatuple = []
    passwords = {}

    for user in users:
        password = generate_password()
        user.password = make_password(password)
        user.activation_token = uuid.uuid4()
        user.activation_token_expires_at = timezone.now() + timedelta(days=1)
        passwords[user.id] = password
        updated_users.append(user)

    User.objects.bulk_update(
        updated_users, ["password", "activation_token", "activation_token_expires_at"]
    )

    logger.debug(f"Generated passwords: {passwords}")

    print(passwords)

    pass

    # if settings.STAGE == "PROD":
    #     frontend_url = settings.FRONTEND_URL
    #     with get_connection() as connection:
    #         for user in users:
    #             activation_url = f"{frontend_url}activate/{user.activation_token}/"
    #             context = {
    #                 "user": user,
    #                 "activation_url": activation_url,
    #                 "password": passwords[user.id],
    #             }

    #             subject = "Activate your Protos education Account"
    #             html_message = render_to_string("activation_email.html", context)
    #             plain_message = strip_tags(html_message)

    #             email = EmailMultiAlternatives(
    #                 subject,
    #                 plain_message,
    #                 settings.DEFAULT_FROM_EMAIL,
    #                 [user.email],
    #                 connection=connection,
    #             )
    #             email.attach_alternative(html_message, "text/html")
    #             try:
    #                 email.send()
    #                 logger.info(f"✅ Sent activation email to {user.email}")
    #             except Exception as e:
    #                 logger.error(f"❌ Failed to send email to {user.email}: {e}")
    return f"Processed {len(users)} users."


@shared_task
def send_activation_email(user_id, password):
    user = User.objects.get(pk=user_id)
    user.activation_token = uuid.uuid4()
    user.activation_token_expires_at = timezone.now() + timedelta(days=1)
    user.save()
    activation_url = f"{frontend_url}activate/{user.activation_token}/"
    context = {"user": user, "activation_url": activation_url, "password": password}
    subject = "Activate your protosedu Account"
    html_message = render_to_string("activation_email.html", context)
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    to = user.email

    msg = EmailMultiAlternatives(subject, plain_message, from_email, [to])
    msg.attach_alternative(html_message, "text/html")
    msg.send()


@shared_task
def send_password_reset_request_email(user_id):
    user = User.objects.get(pk=user_id)
    reset_password_url = f"{frontend_url}reset-password/{user.reset_password_token}/"
    context = {"user": user, "reset_password_url": reset_password_url}
    subject = "Password reset protosedu account"
    html_message = render_to_string("password_reset_request_email.html", context)
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    to = user.email

    msg = EmailMultiAlternatives(subject, plain_message, from_email, [to])
    msg.attach_alternative(html_message, "text/html")
    msg.send()


def is_losing_streak(last_date):
    now = timezone.now()
    today = now.date()

    if last_date != today:
        return True
    return False


@shared_task
def check_streaks():
    now = timezone.now()
    today = now.date()

    students = Student.objects.all()
    for student in students:
        if student.last_task_completed_at:
            last_date = student.last_task_completed_at.date()
            if is_losing_streak(last_date):
                student.streak = 0
                student.save()
            else:
                return
        else:
            student.streak = 0
            student.save()

    parents = Parent.objects.all()
    for parent in parents:
        for child in parent.children.all():
            if child.last_task_completed_at:
                last_date = child.last_task_completed_at.date()
                if is_losing_streak(last_date):
                    child.streak = 0
                    child.save()
                else:
                    return
            else:
                child.streak = 0
                child.save()


@shared_task
def delete_expired_subscriptions():
    subscriptions = Subscription.objects.all().select_related("user")

    inactive_subscriptions = [sub for sub in subscriptions if not sub.is_active]

    datatuple = []
    for subscription in inactive_subscriptions:
        user = subscription.user
        context = {"user": user}
        html_message = render_to_string("subscription_expired_email.html", context)
        plain_message = strip_tags(html_message)
        msg = (
            "Your subscription has expired",
            plain_message,
            html_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        datatuple.append(msg)

    # Send all emails
    send_mass_html_mail(datatuple, fail_silently=False)

    # Delete expired subscriptions
    count = len(inactive_subscriptions)
    for subscription in inactive_subscriptions:
        subscription.delete()

    return f"Deleted {count} expired subscriptions"


@shared_task
def send_user_credentials_to_admins(file_path, school_name):
    subject = f"Credentials for {school_name} "
    body = "Attached is the Excel file containing newly generated user credentials."

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=settings.ADMIN_EMAILS,
    )
    email.attach_file(file_path)
    email.send(fail_silently=False)

    return f"User credentials file sent to {settings.ADMIN_EMAILS}"


@shared_task
def send_complaint_to_admins(complaint_id):
    """
    Send an email to admins with the details of a complaint.
    """
    complaint = Complaint.objects.get(pk=complaint_id)
    subject = f"New Complaint Received: {complaint.type}"
    body = f"Complaint ID: {complaint.id}\n\nComplaint type: {complaint.type}\n\nDetails: {complaint.description}"

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=settings.ADMIN_EMAILS,
    )
    email.send(fail_silently=False)

    return f"Complaint email sent to {settings.ADMIN_EMAILS}"


@shared_task
def course_invalidate_cache(
    course_id, prefix, item_id=None, user_id=None, child_id=None
):
    try:
        if user_id:
            user = User.objects.get(pk=user_id)
            _invalidate_keys(user, child_id, course_id, prefix, item_id)
        else:
            for user in User.objects.all():
                if hasattr(user, "student"):
                    _invalidate_keys(user, None, course_id, prefix, item_id)
                elif hasattr(user, "parent"):
                    children = Child.objects.filter(parent=user.parent)
                    for child in children:
                        _invalidate_keys(user, child.id, course_id, prefix, item_id)
                else:
                    _invalidate_keys(user, None, course_id, prefix, item_id)
    except Exception as e:
        print(f"[course_invalidate_cache] Error: {e}")


def _invalidate_keys(user, child_id, course_id, prefix, item_id):
    if prefix == "course":
        list_key = get_cache_key(prefix + "s", user, child_id)
    else:
        list_key = get_cache_key(prefix + "s", user, child_id, course=course_id)
    cache.delete(list_key)
    print("Cache invalidated:", list_key)

    if item_id:
        detail_key = get_cache_key(prefix, user, child_id, id=item_id)
        cache.delete(detail_key)
        print("Cache invalidated:", detail_key)


@shared_task
def invalidate_user_cache(user_id):
    """
    Invalidate the cache for a specific user.
    """
    cache_key = f"user_data_{user_id}"
    cache.delete(cache_key)


@shared_task
def generate_daily_messages(languages_list: Optional[List[str]] = None):
    today = timezone.now().date()

    if not languages_list:
        languages = [lang[0] for lang in LANGUAGE_CHOICES]
    else:
        languages = languages_list

    for lang in languages:
        phrases = MotivationalPhrase.objects.filter(language=lang, is_active=True)

        if not phrases.exists():
            print(f"No phrases found for language: {lang}")
            continue

        selected_phrase = random.choice(phrases)
        daily_message, created = DailyMessage.objects.update_or_create(
            date=today,
            language=lang,
            defaults={"message": selected_phrase.text, "is_active": True},
        )

        if created:
            print(
                f"Created daily message for {lang} on {today}: {selected_phrase.text}"
            )
        else:
            print(
                f"Updated daily message for {lang} on {today}: {selected_phrase.text}"
            )
