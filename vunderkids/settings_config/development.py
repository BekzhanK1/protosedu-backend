from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]
CORS_ALLOW_ALL_ORIGINS = True
FRONTEND_URL = "https://protosedu.kz/"
BACKEND_URL = "https://api.protosedu.kz/"

CSRF_TRUSTED_ORIGINS = ["https://*", "http://*"]


# Use secure cookies when serving over HTTPS.
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False