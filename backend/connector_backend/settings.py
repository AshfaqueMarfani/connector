"""
Django settings for connector_backend project.

Production-ready configuration for:
- PostgreSQL + PostGIS (geospatial database)
- Django REST Framework + JWT authentication
- Django Channels (WebSocket support via Redis)
- Celery (async task queue via Redis)
- CORS, security headers, and App Store compliance defaults
"""

from datetime import timedelta
from pathlib import Path

import environ

# ---------------------------------------------------------------------------
# PATH CONFIGURATION
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# ENVIRONMENT VARIABLES
# ---------------------------------------------------------------------------
env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    DB_HOST=(str, "localhost"),
    DB_PORT=(int, 5432),
    REDIS_URL=(str, "redis://localhost:6379/0"),
    CELERY_BROKER_URL=(str, "redis://localhost:6379/1"),
    CELERY_RESULT_BACKEND=(str, "redis://localhost:6379/2"),
    JWT_ACCESS_TOKEN_LIFETIME_MINUTES=(int, 60),
    JWT_REFRESH_TOKEN_LIFETIME_DAYS=(int, 7),
    LOCATION_OBFUSCATION_RADIUS_METERS=(int, 200),
)

# Read .env file if it exists (development only – production uses real env vars)
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

# ---------------------------------------------------------------------------
# CORE SETTINGS
# ---------------------------------------------------------------------------
SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

# ---------------------------------------------------------------------------
# APPLICATION DEFINITION
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    "daphne",  # Must be before django.contrib.staticfiles for ASGI
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",  # GeoDjango for PostGIS support
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "channels",
    "django_celery_beat",
    "django_celery_results",
]

LOCAL_APPS = [
    "apps.accounts",
    "apps.profiles",
    "apps.locations",
    "apps.statuses",
    "apps.moderation",
    "apps.chat",
    "apps.matching",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ---------------------------------------------------------------------------
# MIDDLEWARE
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "connector_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "connector_backend.wsgi.application"
ASGI_APPLICATION = "connector_backend.asgi.application"

# ---------------------------------------------------------------------------
# DATABASE – PostgreSQL with PostGIS
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT"),
        "OPTIONS": {
            "connect_timeout": 10,
        },
        "CONN_MAX_AGE": 600,  # Persistent connections for 10 minutes
    }
}

# ---------------------------------------------------------------------------
# CUSTOM USER MODEL
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

# ---------------------------------------------------------------------------
# PASSWORD VALIDATION
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# ---------------------------------------------------------------------------
# INTERNATIONALIZATION
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# STATIC & MEDIA FILES
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------------------------------------------------------------
# DEFAULT PRIMARY KEY FIELD TYPE
# ---------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# DJANGO REST FRAMEWORK
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "30/minute",
        "user": "120/minute",
    },
    "EXCEPTION_HANDLER": "apps.accounts.exceptions.custom_exception_handler",
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
}

# ---------------------------------------------------------------------------
# SIMPLE JWT
# ---------------------------------------------------------------------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=env("JWT_ACCESS_TOKEN_LIFETIME_MINUTES")
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=env("JWT_REFRESH_TOKEN_LIFETIME_DAYS")
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}

# ---------------------------------------------------------------------------
# DJANGO CHANNELS – Redis backend
# ---------------------------------------------------------------------------
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("REDIS_URL")],
            "capacity": 1500,
            "expiry": 10,
        },
    },
}

# ---------------------------------------------------------------------------
# CELERY
# ---------------------------------------------------------------------------
CELERY_BROKER_URL = env("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300  # 5 minutes hard limit
CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4 minutes soft limit
CELERY_RESULT_EXTENDED = True
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# Celery Beat schedule for periodic AI matching tasks
CELERY_BEAT_SCHEDULE = {
    "expire-old-statuses": {
        "task": "apps.matching.tasks.expire_old_statuses",
        "schedule": timedelta(hours=1),
    },
    "run-batch-matching": {
        "task": "apps.matching.tasks.run_batch_matching",
        "schedule": timedelta(hours=6),
    },
}

# For tests: run tasks synchronously
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)
CELERY_TASK_EAGER_PROPAGATES = env.bool("CELERY_TASK_EAGER_PROPAGATES", default=False)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:3000", "http://127.0.0.1:3000"],
)
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# SECURITY (hardened for production; relaxed via DEBUG in dev)
# ---------------------------------------------------------------------------
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = "DENY"

# Trust X-Forwarded-Proto from Nginx reverse proxy (required for SSL detection)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ---------------------------------------------------------------------------
# APPLICATION-SPECIFIC CONFIGURATION
# ---------------------------------------------------------------------------

# Location obfuscation radius for Private Profiles (meters).
# The exact GPS coordinate is offset by a random vector within this radius
# so that the user's real position is never exposed on the public map.
LOCATION_OBFUSCATION_RADIUS_METERS = env("LOCATION_OBFUSCATION_RADIUS_METERS")

# OpenAI configuration for AI matching agent
OPENAI_API_KEY = env("OPENAI_API_KEY", default="")
OPENAI_MODEL = env("OPENAI_MODEL", default="gpt-4")

# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "connector.log",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
