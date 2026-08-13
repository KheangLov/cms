# CMS — Project Documentation

As-built technical reference for the whole system. For the original spec this was built from, see [`../CMS_BUILD_PROMPT.md`](../CMS_BUILD_PROMPT.md); for how the build actually went (bugs found and fixed, phase by phase), see [`build-report.html`](build-report.html); for the visual design system, see [`design-system.html`](design-system.html).

## Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Tech stack](#tech-stack)
4. [Domain model](#domain-model)
5. [Backend modules](#backend-modules)
6. [Frontend structure](#frontend-structure)
7. [API surface](#api-surface)
8. [Environment variables](#environment-variables)
9. [Development workflow](#development-workflow)
10. [Testing](#testing)
11. [Design system](#design-system)
12. [Security & performance notes](#security--performance-notes)
13. [Known limitations](#known-limitations)

---

## Overview

A single-tenant, bilingual (Khmer/English) content management system, structured like WordPress + Elementor: static **Pages** and chronological **Posts**, both built from the same reusable, nestable **block** system, edited through a drag-and-drop visual builder. Everything — roles, 2FA, social login, an AI writing assistant, real-time notifications, search, comments, activity history — runs behind one Django REST API, consumed by a Nuxt frontend that renders the public site with SSR and the admin dashboard as a client-only SPA.

Built in 11 phases (0 through 10), each verified against a running system before the next began. See the build report for the full history.

## Architecture

```
Browser
  │
  ├─ Public site (/, /[...slug])         → SSR/ISR via Nuxt routeRules, SEO-indexed
  └─ Admin dashboard (/admin/**)          → CSR-only SPA, noindex, JWT-authenticated
        │
        ▼
Nuxt 4 (frontend) ──── HTTP (REST) ────► Django REST Framework (backend:8000)
        │                                        │
        └──── WebSocket (?token=jwt) ───► Django Channels / Daphne
                                                   │
                        ┌──────────────────────────┼───────────────────────────┐
                        ▼                          ▼                           ▼
                  PostgreSQL 18              Valkey (Redis-proto)        Elasticsearch 9.5
                  (system of record)      (cache, Celery broker,      (cms_content search index,
                                            Channels layer)             cms_logs system-log index)
                        │
                        ▼
                  MinIO (S3-compatible)  ← media originals + generated thumbnails, served via
                                            AWS_S3_CUSTOM_DOMAIN, never proxied through Django

Celery worker + beat: thumbnailing, AI provider calls, search indexing, scheduled jobs — all off
the request/response cycle. Kibana reads the cms_logs index for observability.
```

**Rendering strategy:** public routes render with SSR (or prerendered/ISR for static pages) via Nuxt `routeRules`; `/admin/**` is forced `{ ssr: false }` — pure CSR behind auth, since it's never indexed and SSR would only add server load with no SEO upside.

**Auth:** JWT access token lives in memory (Pinia), refresh token is an httpOnly cookie. `frontend/plugins/auth.client.ts` exchanges the refresh cookie for a new access token on every app boot, so a hard reload doesn't require re-login.

## Tech stack

### Backend
| Package | Version |
|---|---|
| Python | 3.13 |
| Django | 5.2.17 LTS |
| djangorestframework | 3.18.0 |
| django-filter | 26.1 |
| drf-spectacular | 0.30.0 |
| channels / channels-redis / daphne | 4.3.2 / 4.3.0 / 4.2.3 |
| celery / django-celery-beat | 5.6.3 / 2.9.0 |
| redis (client) | 5.3.1 — pinned below 8.x, see [Known limitations](#known-limitations) |
| psycopg | 3.3.4 |
| django-storages[boto3] / boto3 | 1.14.6 / 1.43.69 |
| elasticsearch (client) | 9.5.0 |
| Pillow | 12.3.0 |
| djangorestframework-simplejwt | 5.5.1 |
| cryptography | 50.0.0 |
| django-otp | 1.7.0 |
| qrcode | 8.2 |
| django-allauth | 65.19.0 |
| pytest-django / factory_boy | 4.14.0 / 3.3.3 |

### Frontend
| Package | Version |
|---|---|
| Nuxt | 4.5.2 |
| Vue | 3.5.41 |
| Vuetify / vuetify-nuxt-module | 4.1.8 / 1.0.0-rc.4 |
| Tailwind CSS | 4.3.3 |
| Pinia | 4.0.3 |
| @nuxtjs/i18n | 10.6.0 |
| @nuxtjs/color-mode | 4.0.1 |
| @nuxt/image | 2.1.0 |
| vuedraggable | 4.1.0 |
| swiper | 14.1.0 |
| lodash-es | 4.18.1 |
| TypeScript | 6.0.3 |

### Infrastructure
PostgreSQL 18 · Valkey 9.1 (Redis-protocol compatible, BSD-licensed — chosen over Redis after its 2024 license change) · Elasticsearch 9.5.0 + Kibana 9.5.0 · MinIO (S3-compatible object storage) · Docker Compose.

## Domain model

All content models inherit from one of two shared abstract bases in `apps/common/models.py`:
- **`TimestampedModel`** — `created_at`, `updated_at`.
- **`SoftDeleteModel`** (extends `TimestampedModel`) — adds `is_deleted`, `deleted_at`, `deleted_by`. The default manager (`objects`) excludes deleted rows everywhere automatically; `all_objects` is the escape hatch for trash views. `soft_delete()` / `restore()` also write an `ActivityLog` entry.

| Model | Base | Key fields |
|---|---|---|
| `User` (`apps.users`) | `AbstractUser` | `email` (unique, login field), `locale_preference`, `theme_preference` (system/light/dark), `avatar`, 2FA fields (via django-otp) |
| `Role` / `Permission` | Django `Group` / `Permission` | Not custom models — roles are Django Groups, permissions are the auto-generated per-model Django permissions. Admin/Editor/User seeded via data migration. |
| `PageType` (`apps.pages`) | `TimestampedModel` | `name`, `slug`, `is_system` — drives which blocks are available |
| `Page` (`apps.pages`) | `SoftDeleteModel` | `slug`, `page_type` (FK), `status` (draft/published/scheduled/archived), `parent` (self-FK, hierarchical), `comments_enabled`, `publish_at`, `created_by` |
| `PageTranslation` | plain model | `page` (FK), `locale`, `title`, `meta_title`, `meta_description`, `og_image` (FK → Media) |
| `Category` / `Tag` (`apps.posts`) | `TimestampedModel` | hierarchical (Category) / flat (Tag), each with a `*Translation` sibling model |
| `Post` (`apps.posts`) | `SoftDeleteModel` | `slug`, `status`, `category` (FK), `tags` (M2M), `author` (FK User), `featured_image` (FK Media), `published_at`, `comments_enabled` |
| `PostTranslation` | plain model | `post` (FK), `locale`, `title`, `excerpt`, `meta_title`, `meta_description` |
| `BlockType` (`apps.blocks`) | `TimestampedModel` | `name`, `slug`, `category`, `icon`, `prop_schema` (JSON), `is_system` — the extensible block registry |
| `ContentBlock` (abstract) | `SoftDeleteModel` | `block_type` (FK), `parent` (self-FK, nesting), `order`, `props` (JSON) |
| `PageBlock` / `PostBlock` | `ContentBlock` | concrete subclasses with `page` / `post` FK — **not** a `GenericForeignKey`, deliberately, for query performance on the hottest read path |
| `Media` (`apps.media_library`) | `SoftDeleteModel` | `file`, `thumbnail_small`, `thumbnail_medium`, `optimized` (all generated async), `mime_type`, `size_bytes`, `width`/`height`, `processing_status`, `uploaded_by` |
| `Comment` (`apps.comments`) | `SoftDeleteModel` | `content_type` + `object_id` (generic FK to Page or Post), `author`, `parent` (self-FK, threading), `body`, `status` (pending/approved/spam) |
| `Setting` (`apps.settings_app`) | `TimestampedModel` | `key`, `raw_value` (Fernet-encrypted when `is_secret`), `category`, `is_secret`, `description` |
| `ActivityLog` (`apps.activity_log`) | plain model | `actor`, `verb`, `target_type`/`target_id`/`target_repr`, `diff` (JSON), `ip_address`, `timestamp` |

## Backend modules

Each is a Django app under `backend/apps/`.

- **`users`** — custom email-based `User`, JWT auth (register/login/refresh/logout/me), TOTP 2FA (setup/confirm/disable/verify + recovery codes), social login bridge (`social.py`).
- **`roles_permissions`** — read/write API over Django's Group/Permission system; no custom RBAC engine, so new permissions are just new Django model permissions.
- **`settings_app`** — key/value site configuration store; `is_secret` values are Fernet-encrypted at rest (`SETTINGS_ENCRYPTION_KEY`) and used for things like AI provider API keys.
- **`pages`** / **`posts`** — the core content model (see [Domain model](#domain-model)); `pages/resolver.py` exposes `/api/v1/resolve/?path=` so the frontend catch-all route can resolve any URL to a Page (walking its parent hierarchy) or a Post.
- **`media_library`** — upload API + `tasks.py`'s Celery pipeline generating small/medium/optimized WebP variants, notifying the uploader over WebSocket when done.
- **`blocks`** — the extensible `BlockType` registry and `PageBlock`/`PostBlock` nesting/ordering that power the visual builder.
- **`activity_log`** — hybrid audit trail: Django signals catch generic create/update, explicit calls cover publish/unpublish/login/soft-delete/restore. `authentication.py`'s `TrackingJWTAuthentication` records the actor at the moment DRF verifies the JWT (Django's own middleware runs too early to see it). `context.py` holds the request-scoped thread-local state (`get_current_user()`/`get_current_ip()`).
- **`comments`** — threaded, moderated comments on Page or Post via a generic FK, gated by each object's `comments_enabled` flag.
- **`search`** — indexes Page/PageTranslation/PageBlock/Post/PostTranslation/PostBlock into the `cms_content` Elasticsearch index via Celery tasks triggered by signals (`indexing.py`, `signals.py`); `/api/v1/search/` queries it.
- **`ai_agent`** — four provider adapters (`providers.py`: OpenAI, Anthropic, Gemini, generic OpenAI-compatible) reading credentials from `settings_app`; async generate/translate endpoints deliver results over WebSocket when the Celery task completes.
- **`realtime`** — Django Channels wiring: `middleware.py`'s `JWTAuthMiddleware` authenticates WebSocket connections via a `?token=` query param, `consumers.py`'s `NotificationConsumer` serves one Channels group per user (`user_{id}`), `utils.py`'s `notify_user()` is the single entry point every other app calls to push a notification.
- **`common`** — `TimestampedModel` / `SoftDeleteModel` shared bases.
- **`health`** — `/api/v1/health/` checks database, Redis/Valkey, Elasticsearch, and object storage connectivity in one call.

`config/logging_handlers.py`'s `ElasticsearchLogHandler` ships WARNING+ application logs to a separate `cms_logs` index, viewable in Kibana — kept isolated from `cms_content` since the two have different retention/access needs.

## Frontend structure

```
frontend/
  pages/
    index.vue                    Public homepage
    [...slug].vue                Public catch-all — resolves via /api/v1/resolve/, renders blocks
    admin/index.vue               Admin dashboard home (notifications feed)
    admin/login.vue                Login, including the 2FA step and social login buttons
    admin/social-callback.vue      Exchanges the allauth one-time code for a JWT session
    admin/pages/index.vue          Page list
    admin/pages/[id]/index.vue     The drag-and-drop block builder
  components/blocks/
    BlockRenderer.vue              Dispatches a block's `block_type.slug` to the right component
    HeroBlock.vue / TextSectionBlock.vue / SwiperBlock.vue / ColumnsBlock.vue
                                    Shared components — render identically in the builder and the
                                    public site, so what you see while editing is what ships.
  stores/auth.ts                  Pinia store: login, verifyTwoFactor, restoreSession, logout
  composables/useAuthFetch.ts     Fetch wrapper that attaches the JWT and retries once on 401
  composables/useNotifications.ts WebSocket client for the realtime notification feed
  plugins/auth.client.ts          Boots the session from the refresh cookie on every app load
```

Vuetify owns the admin shell; Tailwind owns the public site and the block components shared between builder and renderer (Tailwind's preflight is disabled admin-side so it doesn't fight Vuetify). Both read the same design tokens — see [Design system](#design-system).

## API surface

All routes are under `/api/v1/`. Full interactive reference (including request/response schemas): **http://localhost:8010/api/v1/docs/** (drf-spectacular/Swagger).

| Path prefix | App | Notes |
|---|---|---|
| `auth/register/`, `login/`, `refresh/`, `logout/`, `me/` | users | JWT auth |
| `auth/2fa/setup/`, `confirm/`, `disable/`, `verify/` | users | TOTP 2FA |
| `auth/social/exchange/` | users | Exchanges an allauth one-time code for a JWT pair |
| `roles/`, `permissions/` | roles_permissions | Django Group/Permission CRUD |
| `settings/` | settings_app | Encrypted where `is_secret=true` |
| `pages/`, `page-types/` | pages | + `publish`/`unpublish`/`restore`/`duplicate` actions |
| `posts/`, `categories/`, `tags/` | posts | |
| `media/` | media_library | Upload + async-processed variants |
| `block-types/`, `page-blocks/`, `post-blocks/` | blocks | |
| `activity-log/` | activity_log | Read-only audit trail |
| `comments/` | comments | Threaded, moderated |
| `resolve/?path=` | pages | Page-vs-Post URL resolution for the frontend catch-all route |
| `search/?q=` | search | Elasticsearch-backed |
| `ai/generate/`, `ai/translate/`, `ai/tasks/<id>/`, `ai/providers/` | ai_agent | Async — poll or await the WebSocket notification |
| `health/` | health | No auth required |
| `/ws/notifications/?token=<jwt>` | realtime | WebSocket, not under `/api/v1/` |

Every list endpoint supports pagination, `django-filter`-based `filter`, `search`, and `ordering` query params. Write endpoints follow create/retrieve/update(PATCH+PUT)/delete(=soft delete)/restore consistently.

## Environment variables

Defined in `.env.example` (copy to `.env`) — this is the single source of config for every service in `infra/docker-compose.yml`.

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS` | Standard Django settings |
| `SETTINGS_ENCRYPTION_KEY` | Fernet key encrypting `is_secret` Settings values — generate a real one for anything beyond local dev |
| `POSTGRES_*` | Database connection |
| `REDIS_URL` | Points at Valkey; named `REDIS_URL` because every client library expects that name |
| `ELASTICSEARCH_URL` | Shared by search indexing and system logging |
| `MINIO_ROOT_USER`/`PASSWORD`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_ENDPOINT_URL`, `AWS_S3_CUSTOM_DOMAIN` | Object storage — endpoint is internal (Docker network), custom domain is what's baked into public file URLs, must include the bucket name |
| `GOOGLE_OAUTH_CLIENT_ID`/`SECRET`, `FACEBOOK_OAUTH_CLIENT_ID`/`SECRET` | Blank by default — social login is wired but inert until real OAuth app credentials are supplied |
| `FRONTEND_URL` | Where allauth redirects after a social login round trip |
| `NUXT_PUBLIC_API_BASE` | Browser-side API base (host-published port) |
| `NUXT_API_BASE_INTERNAL` | Server-side (SSR) API base — Docker service name, unaffected by host port remapping |

## Development workflow

```bash
# Bring the whole stack up
docker compose -f infra/docker-compose.yml --env-file .env up -d --build

# Backend code changes: runserver (dev) autoreloads automatically
# Frontend code changes: Nuxt dev server autoreloads automatically
# New Python dependency: rebuild the backend image
docker compose -f infra/docker-compose.yml --env-file .env up -d --build backend

# New npm dependency: install directly in the running container — a named volume
# (frontend_node_modules) shadows whatever a plain image rebuild would produce
docker compose -f infra/docker-compose.yml --env-file .env exec frontend npm install <pkg>

# New Nuxt *page* route: usually picked up live; if it 404s, restart frontend
docker compose -f infra/docker-compose.yml --env-file .env restart frontend

# New Celery task: watchmedo auto-restarts the worker on any .py change automatically

# Migrations
docker compose -f infra/docker-compose.yml --env-file .env exec backend python manage.py makemigrations
docker compose -f infra/docker-compose.yml --env-file .env exec backend python manage.py migrate
```

Only the `backend` service actually runs `migrate` on container start (gated by `RUN_MIGRATIONS=1`) — `celery-worker`/`celery-beat` wait on `backend`'s healthcheck instead of migrating themselves, to avoid a schema-corrupting race between three containers migrating concurrently.

## Testing

```bash
docker compose -f infra/docker-compose.yml --env-file .env exec backend pytest -v
```

`backend/apps/users/tests.py` and `backend/apps/pages/tests.py` cover auth, TOTP 2FA (using `pyotp` to generate real valid codes), page permission boundaries, and soft delete/restore. 10/10 passing as of the last verification pass. Frontend testing (Vitest/Playwright, per the original spec) was not built — manual in-browser verification was used instead for every UI-facing phase.

## Design system

"Ember" — glassmorphism + a warm coral→wine gradient, deliberately not the generic blue-purple AI/SaaS default. One shared token source drives both Vuetify (admin) and Tailwind (public/builder). Full spec in `CMS_BUILD_PROMPT.md` §11; interactive reference with a working light/dark/system toggle in [`design-system.html`](design-system.html).

- **Color:** Ember `#FF6B4A`, Wine `#B0296B`, Gold `#E3B23C`, Ink `#14111C`, Cream `#FBF7F2`, Info `#3873D9`, plus semantic success/error.
- **Type:** Manrope (Latin), Kantumruy Pro (Khmer, via `:lang(km)`) — chosen over Noto Sans Khmer because its proportions actually match Manrope instead of looking visually mismatched next to it.
- **Units:** rem everywhere; px reserved for `@media` breakpoints only, so the UI scales correctly with a user's browser text-zoom setting.
- **Dark mode:** a real feature (`@nuxtjs/color-mode`), not just tokens — system/light/dark, persisted to `localStorage` for anonymous visitors and to `User.theme_preference` for logged-in users.

## Security & performance notes

- DRF throttling on auth/AI endpoints; CORS locked to the Nuxt origin; secrets only via env vars or encrypted Settings values, never committed.
- `select_related`/`prefetch_related` on every relation-traversing serializer; composite index on `(status, published_at)` for the blog-feed query; unique index on every slug field.
- Media reads are presigned URLs straight to MinIO — never proxied through the Django process.
- Search goes through Elasticsearch, not a Postgres `ILIKE` scan.
- Nothing slow runs in the request/response cycle — thumbnailing, AI calls, and search indexing are all async via Celery.

## Known limitations

- **Social login has never completed a real OAuth round trip.** Google/Facebook login is fully wired (routes resolve, invalid exchange codes are correctly rejected) but this environment has no real OAuth app credentials. Add `GOOGLE_OAUTH_CLIENT_ID`/`FACEBOOK_OAUTH_CLIENT_ID` (and secrets) to `.env`, then do one live login per provider before trusting it in production.
- **WebSocket presence and a live admin activity feed were deferred** from Phase 8's scope — only the notification channel was built.
- **A cosmetic DRF pagination warning** on soft-deleted querysets (`SoftDeleteQuerySet` has no explicit default ordering) — harmless at current scale.
- **`redis` (the Python client) is pinned to 5.3.1**, not the newest 8.x — `channels-redis==4.3.0` was never tested against 8.x and every WebSocket connection died with a timeout under it. Re-verify compatibility before bumping.
- **MinIO's open-source edition entered maintenance mode** in December 2025. The app only talks the S3 API, so switching to OpenMaxIO or Garage would be a low-effort change if ever needed.
