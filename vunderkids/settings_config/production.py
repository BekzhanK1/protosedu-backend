from .base import *

DEBUG = True

ALLOWED_HOSTS = [
    "https://protosedu.kz",
    "https://www.protosedu.kz",
    "http://85.198.89.17",
    "http://localhost",
    "http://127.0.0.1",
    "protosedu.kz",
    "www.protosedu.kz",
    "api.protosedu.kz",
    "85.198.89.17",
]


CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://protosedu.kz",
    "https://www.protosedu.kz",
]

CSRF_TRUSTED_ORIGINS = [
    "https://www.protosedu.kz",
    "https://protosedu.kz",
    "https://api.protosedu.kz",
]

FRONTEND_URL = "https://protosedu.kz/"
BACKEND_URL = "https://api.protosedu.kz/"


import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="https://59ec37859ff77bf85e8aeaf1b5465136@o4509047659036672.ingest.de.sentry.io/4509047703666768",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,  # optional: for performance monitoring
    send_default_pii=True,  # optional: if you want to send user info
    _experiments={
        "continuous_profiling_auto_start": True,
    },
)
