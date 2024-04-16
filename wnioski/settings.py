import environ
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

# config only for ZUS service in .env file
env = environ.Env()
env_file = '.env'
env.read_env(env_file=os.path.join(BASE_DIR, ".env"))


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
    "django_filters",
    "webpush",
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS + THIRD_PARTY_APPS
CRISPY_TEMPLATE_PACK = "bootstrap4"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
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
                "applications.requests.context_processors.vapid_key",
            ],
        },
    },
]


WSGI_APPLICATION = "wnioski.wsgi.application"

if get_secret("DEVIL"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": get_secret("DB_NAME"),
            "USER": get_secret("DB_USER"),
            "PASSWORD": get_secret("DB_PASSWORD"),
            "HOST": get_secret("DB_HOST"),
            "PORT": "",
        }
    }
else:
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
# DEFAULT_FROM_EMAIL = get_secret("EMAIL_HOST_USER")

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_USE_TLS = True
EMAIL_HOST = get_secret("EMAIL_HOST")
EMAIL_HOST_USER = get_secret("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = get_secret("EMAIL_HOST_PASSWORD")
EMAIL_PORT = get_secret("EMAIL_PORT")

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

STATIC_URL = "/static/"

if get_secret("DEVIL"):
    STATICFILES_DIRS = [BASE_DIR.child("public").child("static")]
else:
    STATICFILES_DIRS = [BASE_DIR.child("static")]


MEDIA_URL = "/media/"


if get_secret("DEVIL"):
    STATIC_ROOT = os.path.join(BASE_DIR, "public", "staticfiles")
    MEDIA_ROOT = os.path.join(BASE_DIR, "public", "media")
else:
    STATIC_ROOT = BASE_DIR.child("staticfiles")
    MEDIA_ROOT = BASE_DIR.child("media")


WEBPUSH_SETTINGS = {
    "VAPID_PUBLIC_KEY": get_secret("VAPID_PUBLIC_KEY"),
    "VAPID_PRIVATE_KEY": get_secret("VAPID_PRIVATE_KEY"),
    "VAPID_ADMIN_EMAIL": get_secret("ADMIN_EMAIL"),
}

MESSAGE_TAGS = {
    messages.SUCCESS: "alert-success",
    messages.ERROR: "alert-danger",
    messages.WARNING: "alert-warning",
}

LOGGING = {
    "version": 1,
    "loggers": {
        "django": {
            "handlers": ["logfile"],
            "level": "INFO",
            "propagate": True,
        },
        "ezla": {
            "handlers": ["ezlalogfile"],
            "level": "WARNING",
            "propagate": True,
        },
    },
    "handlers": {
        "logfile": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": "wnioski.log",
            "formatter": "verbose",
            "encoding": "utf-8",
        },
        "ezlalogfile": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": "ezlaraporty.log",
            "formatter": "verbose",
            "encoding": "utf-8",
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

LANGUAGE_CODE = "pl"

LOCALE_PATHS = (os.path.join(BASE_DIR, "locale"),)

TIME_ZONE = "Europe/Warsaw"

USE_I18N = True

USE_L10N = True

USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# if not DEBUG:
#     SECURE_SSL_REDIRECT = True
#     SESSION_COOKIE_SECURE = True
#     CSRF_COOKIE_SECURE = True

# settings to extract reports from polish zus, set it to empty string if not the case
# should be placed in .env file
EZLA_LOGIN = env("EZLA_LOGIN", default=None)
EZLA_HASLO = env("EZLA_HASLO", default=None)
EZLA_NIP = env("EZLA_NIP", default=None)
EZLA_EXTRACT_PSWD = env("EZLA_EXTRACT_PSWD", default=None)
EZLA_URL=env("EZLA_URL", default=None)
EZLA_SERVICE_USERNAME=env("EZLA_SERVICE_USERNAME", default=None)
EZLA_SERVICE_PSWD=env("EZLA_SERVICE_PSWD", default=None)
EZLA_SERVICE_IP=env("EZLA_SERVICE_IP", default=None)
