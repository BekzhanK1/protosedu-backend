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
