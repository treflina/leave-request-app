import json
import os

from django.core.exceptions import ImproperlyConfigured
from django.contrib.messages import constants as messages

from unipath import Path

BASE_DIR = Path(__file__).ancestor(2)


with open(os.path.join(BASE_DIR, "secret.json")) as f:
    secret = json.loads(f.read())


def get_secret(secret_name, secrets=secret):
    try:
        return secrets[secret_name]
    except:
        msg = f"Nie mam dostępu do zmiennej {secret_name}"
        raise ImproperlyConfigured(msg)


DEBUG = get_secret("DEBUG")

ALLOWED_HOSTS = get_secret("ALLOWED_HOSTS")

SECRET_KEY = get_secret("SECRET_KEY")


DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_cleanup.apps.CleanupConfig",
]

LOCAL_APPS = [
    "applications.requests",
    "applications.sickleaves",
    "applications.users",
    "applications.home",
]

THIRD_PARTY_APPS = [
    "crispy_forms",
    "simple_history",
    "constrainedfilefield",
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS + THIRD_PARTY_APPS
CRISPY_TEMPLATE_PACK = "bootstrap4"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]

ROOT_URLCONF = "wnioski.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR.child("templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.media",
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "applications.requests.context_processors.number_requests_received",
            ],
        },
    },
]


WSGI_APPLICATION = "wnioski.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": get_secret("DB_NAME"),
        "USER": get_secret("DB_USER"),
        "PASSWORD": get_secret("DB_PASSWORD"),
        "HOST": "localhost",
        "PORT": "3306",
    }
}


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

DEFAULT_FROM_EMAIL = get_secret("DEFAULT_FROM_EMAIL")

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_USE_TLS = True
EMAIL_HOST = get_secret("EMAIL_HOST")
EMAIL_HOST_USER = get_secret("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = get_secret("EMAIL_HOST_PASSWORD")
EMAIL_PORT = get_secret("EMAIL_PORT")

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR.child("static")]
STATIC_ROOT = BASE_DIR.child("staticfiles")

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR.child("media")

MESSAGE_TAGS = {
    messages.SUCCESS: "alert-success",
    messages.ERROR: "alert-danger",
}

LOGGING = {
    "version": 1,
    "loggers": {
        "django": {
            "handlers": ["logfile"],
            "level": "INFO",
            "propagate": True,
        },
    },
    "handlers": {
        "logfile": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": "wnioski.log",
            "formatter": "verbose",
        },
    },
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
}

AUTH_USER_MODEL = "users.User"

LANGUAGE_CODE = "pl-PL"

TIME_ZONE = "Europe/Warsaw"

USE_I18N = True

USE_L10N = True

USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
