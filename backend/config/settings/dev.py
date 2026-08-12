from .base import *  # noqa: F401,F403

DEBUG = True

# Structured logging → Elasticsearch/Kibana — CMS_BUILD_PROMPT.md §5.11.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
        "elasticsearch": {
            "class": "config.logging_handlers.ElasticsearchLogHandler",
            "es_url": ELASTICSEARCH_URL,  # noqa: F405
            "level": "INFO",
        },
    },
    "root": {"handlers": ["console", "elasticsearch"], "level": "INFO"},
    "loggers": {
        # Daphne/Channels' own request-line logging is noisy at INFO and not
        # useful in the log-analytics index — keep it on the console only.
        "django.channels.server": {"handlers": ["console"], "level": "INFO", "propagate": False},
        # CRITICAL: the elasticsearch client itself logs every request it makes
        # via elastic_transport.transport. Left attached to the ES handler, each
        # shipped log line's own indexing request generates another log line,
        # which ships another log line — an infinite feedback loop. Found during
        # Phase 10 verification: 4,225+ documents were created in a few seconds
        # before this was caught. Both loggers must stay console-only.
        "elastic_transport": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "elasticsearch": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}

INSTALLED_APPS += [  # noqa: F405
    "django_extensions",
]
