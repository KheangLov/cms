from pathlib import Path

import environ

# backend/config/settings/base.py -> backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
env_file = BASE_DIR.parent / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

SECRET_KEY = env("DJANGO_SECRET_KEY", default="insecure-dev-key-do-not-use-in-prod")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    # "daphne" must be first — this is what makes `manage.py runserver` ASGI/
    # WebSocket-capable in dev (it patches the runserver command). Without it,
    # runserver is WSGI-only and silently 404s any WebSocket URL through Django's
    # normal HTTP resolver instead of routing it through config/asgi.py. Found
    # while verifying Phase 8 — HTTP endpoints all worked fine either way, so this
    # was invisible until the first real WebSocket connection attempt.
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third-party
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "corsheaders",
    "channels",
    "drf_spectacular",
    # project — see CMS_BUILD_PROMPT.md §7 for the full planned app list;
    # apps are added here as each build phase actually implements them.
    "apps.common",
    "apps.health",
    "apps.users",
    "apps.roles_permissions",
    "apps.settings_app",
    "apps.pages",
    "apps.posts",
    "apps.media_library",
    "apps.blocks",
    "apps.activity_log",
    "apps.comments",
    "apps.search",
    "apps.ai_agent",
    "apps.realtime",
]

AUTH_USER_MODEL = "users.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.activity_log.context.CurrentRequestMiddleware",
]

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------- Database ----------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="cms"),
        "USER": env("POSTGRES_USER", default="cms"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="cms"),
        "HOST": env("POSTGRES_HOST", default="postgres"),
        "PORT": env("POSTGRES_PORT", default="5432"),
        "CONN_MAX_AGE": 60,  # persistent connections — CMS_BUILD_PROMPT.md §6.1
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------- Password validation ----------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------- i18n / l10n — CMS_BUILD_PROMPT.md §5.14 ----------
LANGUAGE_CODE = "en"
LANGUAGES = [
    ("en", "English"),
    ("km", "Khmer"),
]
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------- Static files ----------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# ---------- Valkey / Redis — cache, Celery broker, Channels layer (§2) ----------
# Var is named REDIS_URL because every client library here (redis-py, celery,
# channels-redis) expects that name; the container behind it is Valkey.
REDIS_URL = env("REDIS_URL", default="redis://valkey:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    }
}

# ---------- Celery (§2) ----------
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# ---------- Elasticsearch — §5.11, §5.12 ----------
ELASTICSEARCH_URL = env("ELASTICSEARCH_URL", default="http://elasticsearch:9200")

# ---------- Object storage — MinIO, S3-compatible (§5.3) ----------
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default="cms-media")
# Internal — what Django/boto3 itself uses to talk to MinIO over the Docker network.
AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", default="http://minio:9000")
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default="cms_minio_admin")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default="")
AWS_S3_ADDRESSING_STYLE = "path"
# Public — the domain baked into generated file URLs (Media.file.url etc.), separate
# from the internal endpoint above so a browser can actually load them. "minio:9000"
# only resolves inside the Docker network. Discovered at Phase 3.
AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", default="localhost:9090/cms-media")
AWS_S3_URL_PROTOCOL = "http:"
AWS_DEFAULT_ACL = None
# Dev bucket is public-read (see infra/docker-compose.yml minio-init), so plain URLs
# work with no signature. Phase 3 (Media Library) revisits this for draft/unpublished
# media that needs to stay private — those will want presigned URLs instead.
AWS_QUERYSTRING_AUTH = False

# ---------- CORS ----------
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:3000"])
CORS_ALLOW_CREDENTIALS = True  # the frontend sends/receives the httpOnly refresh cookie cross-origin

# ---------- DRF — CMS_BUILD_PROMPT.md §5.16 ----------
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.activity_log.authentication.TrackingJWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",  # for the browsable API / admin
    ],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "CMS API",
    "DESCRIPTION": "WordPress-inspired CMS — see CMS_BUILD_PROMPT.md at the repo root.",
    "VERSION": "0.1.0",
}

# ---------- JWT auth — §5.4. Access token in the response body, refresh token as an
# httpOnly cookie (see apps/users/views.py) — §10.2's confirmed shape. ----------
from datetime import timedelta  # noqa: E402

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "USER_ID_FIELD": "id",
}

# ---------- Settings module secret encryption — §5.8, apps/settings_app ----------
# Dev-only default below is a syntactically valid Fernet key so the app doesn't crash
# with no .env — generate a real one (`Fernet.generate_key()`) for any shared/prod env.
SETTINGS_ENCRYPTION_KEY = env(
    "SETTINGS_ENCRYPTION_KEY", default="dx39U2u_6sftD3A7dfMr_c7Jz_O01VyST65AbiiFxyU="
)
