"""
Django settings for niki project.

Generated by 'django-admin startproject' using Django 3.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

import os
from datetime import timedelta
from os import environ, getenv
from pathlib import Path

from django.conf.global_settings import LOGOUT_REDIRECT_URL
from dotenv import load_dotenv
from celery.schedules import crontab

load_dotenv(".env")

LDAP = getenv("LDAP", "False") == "True"

WITHLDAP = False
if LDAP:
    try:
        import ldap

        WITHLDAP = True
    except ImportError:
        pass


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = environ["SECRET_KEY"]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = getenv("DEBUG", "False") == "True"
PROD = getenv("PROD", "False") == "True"
COMPRESSION = getenv("RESSOURCES_COMPRESSION", "False") == "True"

RADIUS = getenv("RADIUS", "False") == "True"

ALLOWED_HOSTS = ["*"]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_celery_beat",
    "health_check",
    "health_check.db",
    "health_check.cache",
    "health_check.storage",
    "health_check.contrib.migrations",
    "appuser",
    "appmacgest",
    "appkfet",
    "appevents",
    "rest_framework",
    "corsheaders",
    "api",
    "captcha",
    "lydia",
]

if WITHLDAP:
    INSTALLED_APPS.append("ldapdb")

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if PROD:
    security_middleware_index = MIDDLEWARE.index("django.middleware.security.SecurityMiddleware")
    MIDDLEWARE.insert(security_middleware_index, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "niki.urls"

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
                "niki.context_processors.get_utilisateur",
                "niki.context_processors.get_consommateur",
            ],
            "libraries": {
                "project_tags": "templatetags.extra_filters",
                "admin.urls": "django.contrib.admin.templatetags.admin_urls",
            },
        },
    },
]

WSGI_APPLICATION = "niki.wsgi.application"

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    "default": __import__("db").DB_SETTINGS,
}

if WITHLDAP:
    DATABASES["ldap"] = __import__("db").LDAP_SETTINGS

if RADIUS:
    DATABASES["radcheck"] = __import__("db").RADIUS_SETTINGS

DATABASE_ROUTERS = ["niki.dbrouter.DBRouter"]

if WITHLDAP:
    DATABASE_ROUTERS.append("ldapdb.router.Router")

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

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

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 25,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

# CORS: https://github.com/adamchainz/django-cors-headers
if PROD:
    CORS_ALLOWED_ORIGINS = URL_CORS.split(" ") if " " in (URL_CORS := getenv("URL_CORS", "")) else URL_CORS
else:
    # FOR DEV ONLY!!
    CORS_ALLOW_ALL_ORIGINS = True

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = "fr-FR"

TIME_ZONE = "Europe/Paris"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# CSRF validation
if PROD:
    URL_CSRF = getenv("URL_CSRF", "")
    CSRF_TRUSTED_ORIGINS = [URL_CSRF]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = "/static/"

if PROD:
    STATIC_ROOT = BASE_DIR / "static"
else:
    STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"

# Auto compression of static ressources and caching
if PROD and COMPRESSION:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Niki specific parameters
CAPTCHA_FONT_SIZE = 36
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "index"
LOGOUT_REDIRECT_URL = "index"

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = getenv("EMAIL_HOST", "")
EMAIL_HOST_USER = getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = getenv("DEFAULT_FROM_EMAIL", "")
SERVER_EMAIL = getenv("SERVER_EMAIL", "")

LYDIA_URL = getenv("LYDIA_URL", "")
VENDOR_TOKEN = getenv("LYDIA_VENDOR_TOKEN", "")
CASHIER_PHONE = getenv("LYDIA_CASHIER_PHONE", "")


# Celery settings
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_BROKER_URL = getenv("CELERY_BROKER_URL", "amqp://localhost")
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'

if DEBUG and not PROD:
    BROKER_BACKEND = "memory"
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True


CELERYBEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

CELERY_BEAT_SCHEDULE = {
    "check_user_cotiz_task": {
        "task": "appuser.tasks.check_user_cotiz_task",
        "schedule": crontab(minute=0, hour=0),
    },
    "send_mail_for_cotiz_task": {
        "task": "appuser.tasks.send_mail_for_cotiz_task",
        "schedule": crontab(minute=0, hour=0),
    },
}
