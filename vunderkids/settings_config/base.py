# settings/base.py

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "your-default-secret-key")

DEBUG = False
STAGE = os.getenv("STAGE", "DEV")

CACHE_STAGE = os.getenv("CACHE_STAGE", "docker")
CELERY_STAGE = os.getenv("CELERY_STAGE", "docker")
CHANNELS_STAGE = os.getenv("CHANNELS_STAGE", "docker")


ADMIN_EMAILS = [
    email.strip() for email in os.getenv("ADMIN_EMAILS", "").split(",") if email.strip()
]

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "drf_spectacular",
    "corsheaders",
    "rest_framework",
    "api",
    "account",
    "tasks",
    "subscription",
    "modo",
    "leagues",
    "documents",
    "ai_tutor",
    "storages",
]
if STAGE == "DEV":
    INSTALLED_APPS += [
        "silk",
    ]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "100/minute", "user": "1000/minute"},
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}


if CHANNELS_STAGE == "docker":
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [("redis", 6379)],
            },
        },
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [("localhost", 6379)],
            },
        },
    }


if CACHE_STAGE == "docker":
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://redis:6379/1",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
        }
    }

elif CACHE_STAGE == "localhost":
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://localhost:6379/1",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
        }
    }

elif CACHE_STAGE == "local":
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://redis:6379/1",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
        }
    }

else:
    raise SystemError(
        "CACHE_STAGE must be either 'docker', 'localhost', or 'local'. Please check your .env file."
    )


SPECTACULAR_SETTINGS = {
    "TITLE": "vunderkids API",
    "DESCRIPTION": "This is API for e-learning system that is served on https://vunderkids.kz",
    "VERSION": "v1",
    "CONTACT": {
        "name": "Bekzhan Kimadieff",
        "email": "bkimadieff@gmail.com",
    },
    "SERVE_INCLUDE_SCHEMA": False,  # This hides the schema endpoint from the documentation
    # ADDITIONAL SETTINGS IF NEEDED
}

from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
}

MIDDLEWARE = [
    # "vunderkids.middleware.CheckIPAddressMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if STAGE == "DEV":
    MIDDLEWARE.insert(1, "silk.middleware.SilkyMiddleware")

ROOT_URLCONF = "vunderkids.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "vunderkids.wsgi.application"
ASGI_APPLICATION = "vunderkids.asgi.application"

AUTH_USER_MODEL = "account.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTHENTICATION_BACKENDS = [
    "account.backends.UsernameBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AWS_ACCESS_KEY_ID = os.getenv("YANDEX_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("YANDEX_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("YANDEX_BUCKET_NAME")
AWS_S3_ENDPOINT_URL = "https://storage.yandexcloud.kz"
AWS_S3_REGION_NAME = "kz1"
AWS_S3_SIGNATURE_VERSION = "s3"
AWS_S3_ADDRESSING_STYLE = "path"


LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Aqtau"
USE_I18N = True
USE_TZ = False

STATIC_URL = "/staticfiles/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.storage.yandexcloud.kz/media/"
# DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "school@protosedu.kz"
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = "school@protosedu.kz"

HALYK_TERMINAL_ID = os.getenv("HALYK_TERMINAL_ID")
HALYK_CLIENT_ID = os.getenv("HALYK_CLIENT_ID")
HALYK_CLIENT_SECRET = os.getenv("HALYK_CLIENT_SECRET")

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"

QUESTION_REWARD = 5


DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
DATABASE_TYPE = os.getenv("DATABASE_TYPE")
STAGE = os.getenv("STAGE")


if DATABASE_TYPE == "POSTGRES" or STAGE == "PROD":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": DATABASE_NAME,
            "USER": DATABASE_USER,
            "PASSWORD": DATABASE_PASSWORD,
            "HOST": DATABASE_HOST,
            "PORT": 5432,
        }
    }
    print("POSTGRES IS RUNNING")
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
        }
    }
    print("SQLITE IS RUNNING")


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "root": {
        "handlers": ["sentry"],
        "level": "ERROR",
    },
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} - {message}",
            "style": "{",
        },
    },
    "handlers": {
        "activation": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "activation_tasks.log"),
            "formatter": "verbose",
        },
        "ip-address": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "ip_address.log"),
            "formatter": "verbose",
        },
        "sentry": {
            "level": "ERROR",  # Only capture warnings/errors
            "class": "sentry_sdk.integrations.logging.EventHandler",
        },
    },
    "loggers": {
        "activation": {
            "handlers": ["activation"],
            "level": "DEBUG",
            "propagate": False,
        },
        "ip-address": {
            "handlers": ["ip-address", "sentry"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django": {
            "handlers": ["sentry"],
            "level": "ERROR",
            "propagate": True,
        },
    },
    "filters": {},
}

# if STAGE == "DEV":
#     LOGGING["formatters"].update(
#         {
#             "sql": {
#                 "format": "[{asctime}] {message}",
#                 "style": "{",
#             },
#         }
#     )
#     LOGGING["handlers"].update(
#         {
#             "console": {
#                 "level": "DEBUG",
#                 "class": "logging.StreamHandler",
#                 "formatter": "sql",
#                 "filters": ["slow_queries"],
#             },
#         }
#     )
#     LOGGING["loggers"].update(
#         {
#             "django.db.backends": {
#                 "handlers": ["console"],
#                 "level": "DEBUG",
#                 "propagate": False,
#             },
#         }
#     )
#     LOGGING["filters"].update(
#         {
#             "slow_queries": {
#                 "()": "django.utils.log.CallbackFilter",
#                 "callback": lambda record: "SELECT" in record.getMessage()
#                 and getattr(record, "duration_time", 0) > 0.1,
#             },
#         }
#     )

if CELERY_STAGE == "docker":
    CELERY_BROKER_URL = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND = "redis://redis:6379/0"
elif CELERY_STAGE == "local":
    CELERY_BROKER_URL = "sqla+sqlite:///celerydb.sqlite"
    CELERY_RESULT_BACKEND = "db+sqlite:///celerydb.sqlite"
else:
    raise SystemError(
        "CELERY_STAGE must be either 'docker' or 'local'. Please check your .env file."
    )

STUDENT_DEFAULT_PASSWORD = os.getenv("STUDENT_DEFAULT_PASSWORD", "qwerty123")
STUDENT_DEFAULT_EMAIL = os.getenv("STUDENT_DEFAULT_EMAIL", "lordyestay@gmail.com")
