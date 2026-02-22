import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = "p6b$i%36e_xg%*ok+55@uc(h9)#g+2fj#p%7g#-@y8s6+10q#7"
DEBUG = True
ALLOWED_HOSTS = ["localhost", "0.0.0.0"]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Internal apps
    "example.books",
    "example.coffee",
    "example.www",
    # Include django-unicorn package
    "django_unicorn",
    # Include internal unicorn app
    "example.unicorn",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "example.project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "example.project.wsgi.application"


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}
# CACHES["default"] = {
#     "BACKEND": "django_redis.cache.RedisCache",
#     "LOCATION": "redis://localhost:6379",
#     "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
# }

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
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


LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True


STATIC_URL = "/static/"
STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

UNICORN = {
    "SERIAL": {
        "ENABLED": True,
        "TIMEOUT": 5,
    },
    "CACHE_ALIAS": "default",
    "MORPHER": {
        # "NAME": "alpine",
        "NAME": "morphdom",
        "RELOAD_SCRIPT_ELEMENTS": True,
    },
    "MINIFIED": False,
}


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "django.server": {
            "handlers": ["null"],
            "level": "INFO",
            "propagate": False,
        },
        "profile": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django_unicorn": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}


MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")