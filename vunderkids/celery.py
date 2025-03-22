from __future__ import absolute_import, unicode_literals

import os

from celery import Celery
from celery.schedules import crontab

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vunderkids.settings")

app = Celery("vunderkids")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

from django.conf import settings

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print("Request: {0!r}".format(self.request))


# celery.py or where you configure Celery
if settings.STAGE == "PROD":
    app.conf.beat_schedule = {
        "send_daily_email_to_all_students": {
            "task": "account.tasks.send_daily_email_to_all_students",
            "schedule": crontab(hour=20, minute=15),
        },
        "send_daily_email_to_all_parents": {
            "task": "account.tasks.send_daily_email_to_all_parents",
            "schedule": crontab(hour=20, minute=30),
        },
        "check-streaks-every-night": {
            "task": "account.tasks.check_streaks",
            "schedule": crontab(hour=23, minute=58),
        },
        "delete-expired-subscriptions-every-night": {
            "task": "account.tasks.delete_expired_subscriptions",
            "schedule": crontab(hour=2, minute=2),
        },
    }
else:
    print("Celery is running in development mode")
