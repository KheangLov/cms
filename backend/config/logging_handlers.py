import datetime
import logging


class ElasticsearchLogHandler(logging.Handler):
    """CMS_BUILD_PROMPT.md §5.11 — ships structured application/system logs to a
    dedicated ES index, separate from apps/search's cms_content (§5.12) which
    indexes Page/Post for site search — different retention/access needs.

    Best-effort and synchronous: a slow or briefly-unreachable ES must never
    crash the request it's logging or turn into a cascading failure, so any
    exception here is swallowed rather than propagated. A production-scale
    deployment would offload this to a queue (Celery task, or ship via
    Filebeat/Logstash reading stdout instead) rather than index inline on every
    log call — acceptable trade-off at this project's current scale, called out
    explicitly rather than silently glossed over.
    """

    INDEX_NAME = "cms_logs"

    def __init__(self, es_url):
        super().__init__()
        self.es_url = es_url
        self._client = None

    def _get_client(self):
        if self._client is None:
            from elasticsearch import Elasticsearch

            self._client = Elasticsearch(self.es_url)
        return self._client

    def emit(self, record):
        try:
            client = self._get_client()
            client.index(
                index=self.INDEX_NAME,
                document={
                    "timestamp": datetime.datetime.fromtimestamp(record.created, tz=datetime.UTC).isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "path": record.pathname,
                    "line": record.lineno,
                },
            )
        except Exception:  # noqa: BLE001 — logging must never itself crash the app
            pass
