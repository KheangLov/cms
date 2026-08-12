from .base import *  # noqa: F401,F403

DEBUG = True

# Structured JSON logging → Elasticsearch/Kibana (§5.11) is built out in Phase 10.
# Plain console logging is enough while there's no log shipper running yet.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}

INSTALLED_APPS += [  # noqa: F405
    "django_extensions",
]
