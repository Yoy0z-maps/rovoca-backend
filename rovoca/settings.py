"""Django settings for Rovoca.

The defaults are suitable for local development. Production values are supplied
through environment variables so the same image can run on Cloud Run without
embedding credentials in the container.
"""

import os
from datetime import timedelta
from pathlib import Path

from decouple import Csv, config
from django.core.exceptions import ImproperlyConfigured


BASE_DIR = Path(__file__).resolve().parent.parent
RUNNING_ON_CLOUD_RUN = bool(os.environ.get("K_SERVICE"))


def read_pem_setting(name: str, fallback_filename: str) -> str:
    """Read a PEM value from an env var or a local, git-ignored file."""

    value = config(name, default="")
    if value:
        return value.replace("\\n", "\n")

    configured_path = config(f"{name}_FILE", default=str(BASE_DIR / fallback_filename))
    path = Path(configured_path)
    return path.read_text() if path.is_file() else ""


DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024

SECRET_KEY = config("SECRET_KEY", default="unsafe-development-key")
DEBUG = config("DEBUG", default=False, cast=bool)

if RUNNING_ON_CLOUD_RUN and SECRET_KEY == "unsafe-development-key":
    raise ImproperlyConfigured("SECRET_KEY must be configured on Cloud Run.")

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1,.run.app,api.rovoca.site",
    cast=Csv(),
)
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="https://*.run.app,https://api.rovoca.site",
    cast=Csv(),
)

AUTH_USER_MODEL = "users.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 15,
}

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "django_filters",
    "corsheaders",
    "storages",
    "rest_framework_simplejwt.token_blacklist",
    "word",
    "notice",
    "users.apps.UsersConfig",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

STORAGE_BACKEND = config("STORAGE_BACKEND", default="local").lower()

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

if STORAGE_BACKEND == "gcs":
    bucket_name = config("GS_BUCKET_NAME", default="")
    if not bucket_name:
        raise ImproperlyConfigured("GS_BUCKET_NAME is required when STORAGE_BACKEND=gcs.")

    querystring_auth = config("GS_QUERYSTRING_AUTH", default=True, cast=bool)
    gcs_options = {
        "bucket_name": bucket_name,
        "project_id": config("GS_PROJECT_ID", default=None),
        "default_acl": None,
        "querystring_auth": querystring_auth,
        "file_overwrite": False,
    }
    if querystring_auth:
        gcs_options["iam_sign_blob"] = config(
            "GS_IAM_SIGN_BLOB", default=RUNNING_ON_CLOUD_RUN, cast=bool
        )
        service_account_email = config("GS_SA_EMAIL", default="")
        if service_account_email:
            gcs_options["sa_email"] = service_account_email

    STORAGES["default"] = {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": gcs_options,
    }
    MEDIA_URL = config(
        "MEDIA_URL",
        default=f"https://storage.googleapis.com/{bucket_name}/",
    )
elif STORAGE_BACKEND == "s3":
    bucket_name = config("AWS_STORAGE_BUCKET_NAME", default="yoy0z-maps-blog-bucket")
    region_name = config("AWS_S3_REGION_NAME", default="ap-northeast-2")
    custom_domain = config(
        "AWS_S3_CUSTOM_DOMAIN",
        default=f"{bucket_name}.s3.{region_name}.amazonaws.com",
    )
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "access_key": config("AWS_ACCESS_KEY_ID"),
            "secret_key": config("AWS_SECRET_ACCESS_KEY"),
            "bucket_name": bucket_name,
            "region_name": region_name,
            "custom_domain": custom_domain,
            "file_overwrite": False,
        },
    }
    MEDIA_URL = config("MEDIA_URL", default=f"https://{custom_domain}/")
elif STORAGE_BACKEND != "local":
    raise ImproperlyConfigured(
        f"Unsupported STORAGE_BACKEND={STORAGE_BACKEND!r}; use local, s3, or gcs."
    )

CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = "rovoca.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "rovoca.wsgi.application"

DB_ENGINE = config("DB_ENGINE", default="postgresql").lower()
if DB_ENGINE == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": config("DB_NAME", default=str(BASE_DIR / "db.sqlite3")),
        }
    }
elif DB_ENGINE == "postgresql":
    database_options = {}
    db_sslmode = config("DB_SSLMODE", default="")
    if db_sslmode:
        database_options["sslmode"] = db_sslmode

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("DB_NAME", default="rovoca"),
            "USER": config("DB_USER", default="rovoca"),
            "PASSWORD": config("DB_PASSWORD", default=""),
            "HOST": config("DB_HOST", default="127.0.0.1"),
            "PORT": config("DB_PORT", default="5432"),
            "CONN_MAX_AGE": config("DB_CONN_MAX_AGE", default=60, cast=int),
            "CONN_HEALTH_CHECKS": True,
            "OPTIONS": database_options,
        }
    }
else:
    raise ImproperlyConfigured(
        f"Unsupported DB_ENGINE={DB_ENGINE!r}; use postgresql or sqlite."
    )

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
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

PRIVATE_KEY = read_pem_setting("JWT_PRIVATE_KEY", "private.pem")
PUBLIC_KEY = read_pem_setting("JWT_PUBLIC_KEY", "public.pem")

if RUNNING_ON_CLOUD_RUN and (not PRIVATE_KEY or not PUBLIC_KEY):
    raise ImproperlyConfigured(
        "JWT_PRIVATE_KEY and JWT_PUBLIC_KEY must be configured on Cloud Run."
    )

SIMPLE_JWT = {
    "ALGORITHM": "RS256",
    "SIGNING_KEY": PRIVATE_KEY,
    "VERIFYING_KEY": PUBLIC_KEY,
    "ACCESS_TOKEN_LIFETIME": timedelta(days=7),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=90),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

# Cloud Run terminates TLS before forwarding the request to Gunicorn.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=not DEBUG, cast=bool)
SECURE_HSTS_SECONDS = config(
    "SECURE_HSTS_SECONDS",
    default=31536000 if RUNNING_ON_CLOUD_RUN else 0,
    cast=int,
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS",
    default=RUNNING_ON_CLOUD_RUN,
    cast=bool,
)
SECURE_HSTS_PRELOAD = config(
    "SECURE_HSTS_PRELOAD",
    default=RUNNING_ON_CLOUD_RUN,
    cast=bool,
)
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
