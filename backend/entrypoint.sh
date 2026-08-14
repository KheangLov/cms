#!/bin/sh
set -e

echo "Waiting for postgres at ${POSTGRES_HOST:-postgres}:${POSTGRES_PORT:-5432}..."
until python -c "
import os, sys, psycopg
try:
    psycopg.connect(
        host=os.environ.get('POSTGRES_HOST', 'postgres'),
        port=os.environ.get('POSTGRES_PORT', '5432'),
        dbname=os.environ.get('POSTGRES_DB', 'cms'),
        user=os.environ.get('POSTGRES_USER', 'cms'),
        password=os.environ.get('POSTGRES_PASSWORD', 'cms'),
        connect_timeout=2,
    ).close()
except Exception:
    sys.exit(1)
"; do
  sleep 1
done
echo "Postgres is up."

# Only one process may run migrations — with backend, celery-worker, and celery-beat
# all starting from this same entrypoint, running `migrate` in all three race-condition
# corrupted the schema at Phase 0 (concurrent ALTER TABLE from two processes). Only the
# service with RUN_MIGRATIONS=1 (backend, set in docker-compose.yml) runs it; the others
# just wait for postgres above and depend on backend's healthcheck to know it's done.
if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  python manage.py migrate --noinput
fi

exec "$@"
