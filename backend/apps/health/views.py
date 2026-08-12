import redis
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError
from elasticsearch import Elasticsearch
from elasticsearch import exceptions as es_exceptions
from rest_framework.response import Response
from rest_framework.views import APIView

import boto3


def _check_database():
    try:
        connections["default"].cursor()
        return True, "ok"
    except OperationalError as exc:
        return False, str(exc)


def _check_redis():
    try:
        client = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        client.ping()
        return True, "ok"
    except redis.RedisError as exc:
        return False, str(exc)


def _check_elasticsearch():
    try:
        client = Elasticsearch(settings.ELASTICSEARCH_URL, request_timeout=2)
        return (True, "ok") if client.ping() else (False, "ping failed")
    except es_exceptions.ApiError as exc:
        return False, str(exc)
    except Exception as exc:  # noqa: BLE001 — connection-level failures aren't ApiError
        return False, str(exc)


def _check_object_storage():
    try:
        client = boto3.client(
            "s3",
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        client.list_buckets()
        return True, "ok"
    except (BotoCoreError, ClientError) as exc:
        return False, str(exc)


class HealthCheckView(APIView):
    """
    Verifies every infrastructure dependency is reachable — the entire point of the
    Phase 0 infra skeleton (CMS_BUILD_PROMPT.md §9). Unauthenticated: used by Docker
    healthchecks (§8) and the frontend's own connectivity check.
    """

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        checks = {
            "database": _check_database(),
            "redis": _check_redis(),
            "elasticsearch": _check_elasticsearch(),
            "object_storage": _check_object_storage(),
        }
        results = {name: {"ok": ok, "detail": detail} for name, (ok, detail) in checks.items()}
        overall_ok = all(ok for ok, _ in checks.values())
        return Response(
            {"status": "healthy" if overall_ok else "degraded", "checks": results},
            status=200 if overall_ok else 503,
        )
