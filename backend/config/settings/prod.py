from .base import *  # noqa: F401,F403

DEBUG = False

SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)  # noqa: F405
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Structured logging → Elasticsearch/Kibana — CMS_BUILD_PROMPT.md §5.11.
# Sentry (§2.1, optional) and nginx TLS termination are deployment-environment
# concerns, not something to hardcode into this settings file.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
        "elasticsearch": {
            "class": "config.logging_handlers.ElasticsearchLogHandler",
            "es_url": ELASTICSEARCH_URL,  # noqa: F405
            "level": "WARNING",
        },
    },
    "root": {"handlers": ["console", "elasticsearch"], "level": "WARNING"},
    "loggers": {
        # See dev.py — without this, the ES client's own request logging feeds
        # back into itself via the elasticsearch handler, indexing forever.
        "elastic_transport": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "elasticsearch": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}
