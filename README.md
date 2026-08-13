# CMS

A WordPress/Elementor-inspired content management system: dynamic pages and posts, a drag-and-drop visual page builder with reusable blocks, role-based permissions, 2FA + social login, an AI content-assist agent (bring your own API key), real-time notifications, full-text search, bilingual (Khmer/English) content, and centralized logging — built as a Django REST + Nuxt monorepo, fully containerized.

All 10 build phases are complete and verified end-to-end. The Nuxt admin dashboard has full CRUD parity with everything the backend exposes — pages, posts, media, users, roles, settings, comments, activity log — so **the backend is REST-API-only**; Django's own `/admin/` site is not mounted. See [`docs/PROJECT_DOCUMENTATION.md`](docs/PROJECT_DOCUMENTATION.md) for the full technical reference, and [`docs/build-report.html`](docs/build-report.html) for how it was built (every bug found and fixed, phase by phase).

## Quick start

```bash
cp .env.example .env
docker compose -f infra/docker-compose.yml --env-file .env up -d --build
```

First boot creates the Postgres schema and Elasticsearch indices automatically. Create an admin user once the backend is healthy — this is also your login for the Nuxt admin dashboard, since there's no separate Django admin anymore:

```bash
docker compose -f infra/docker-compose.yml --env-file .env exec backend python manage.py createsuperuser
```

| Service | URL |
|---|---|
| Public site | http://localhost:3000 |
| Admin dashboard | http://localhost:3000/admin |
| Backend API | http://localhost:8010 |
| API docs (Swagger) | http://localhost:8010/api/v1/docs/ |
| Kibana (logs) | http://localhost:5601 |
| MinIO console | http://localhost:9091 |
| PostgreSQL (for pgAdmin/DBeaver/etc.) | `localhost:5432` — db `cms`, user `cms`, password `cms` (from `.env`) |

Check everything came up healthy:

```bash
docker compose -f infra/docker-compose.yml --env-file .env ps
curl http://localhost:8010/api/v1/health/
```

Run the backend test suite:

```bash
docker compose -f infra/docker-compose.yml --env-file .env exec backend pytest -v
```

## Repository layout

```
backend/    Django REST + Channels — apps/ has one Django app per domain (see docs/PROJECT_DOCUMENTATION.md)
frontend/   Nuxt 4 — Vuetify admin shell, Tailwind public site, shared block components
infra/      docker-compose.yml — the whole stack: Postgres, Valkey, Elasticsearch, Kibana, MinIO, backend, Celery, frontend
docs/       Full documentation, design system reference, and the build report
```

## Documentation

- **[docs/PROJECT_DOCUMENTATION.md](docs/PROJECT_DOCUMENTATION.md)** — architecture, domain model, every module's features, API surface, environment variables, testing, deployment notes, known open items.
- **[docs/design-system.html](docs/design-system.html)** — "Ember" visual design system: palette, typography, glassmorphism/gradient rules, and themed component previews. Open directly in a browser.
- **[docs/build-report.html](docs/build-report.html)** — phase-by-phase build history: what was built, what broke, and how it was fixed. Open directly in a browser.
- **[CMS_BUILD_PROMPT.md](CMS_BUILD_PROMPT.md)** — the original build specification this project was built from.

## Tech stack

Django 5.2 LTS + DRF + Channels, PostgreSQL 18, Valkey, Elasticsearch + Kibana, MinIO, Celery — behind Nuxt 4 + Vuetify + Tailwind + Pinia. Full pinned versions in [docs/PROJECT_DOCUMENTATION.md](docs/PROJECT_DOCUMENTATION.md#tech-stack).
