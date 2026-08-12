# Build Prompt: WordPress-Inspired Fullstack CMS Platform

> **How to use this document:** This is the master specification/prompt for building the project. It's written to be handed to an engineer (human or AI) as the source of truth. It is too large to build in one pass — see [Section 9: Recommended Build Phases](#9-recommended-build-phases) for sequencing. Items marked **🔶 Open Question** are decisions the product owner still needs to make; reasonable defaults are proposed so work isn't blocked, but confirm before treating them as final.

---

## 1. Project Overview

Build a fullstack, self-hosted **Content Management System** inspired by WordPress (content model, roles/plugins-like extensibility) and **Elementor** (visual page building). Non-technical users log into an admin dashboard, build pages visually from reusable content blocks, publish bilingual (Khmer/English) content, manage media, and optionally use AI to help generate or translate content. The system must be production-grade: proper auth/permissions, audit trails, soft delete, search, centralized logging, and real-time updates.

---

## 2. Tech Stack

Every row must run its **latest stable release at setup time**, pinned exactly in `requirements/*.txt` and `package.json` lockfiles (never floating ranges for a project this size). The versions below were verified via web research on **2026-08-12** — re-verify immediately before scaffolding, since several of these move fast and the below has already caught two moves this year (Nuxt 3→4, ES 8→9).

| Layer | Choice | Latest stable (verified 2026-08-12) | Notes |
|---|---|---|---|
| Language | Python | **3.13** | 3.14 expected ~Oct 2026 (Python's fixed annual cadence) |
| Backend API | Django + Django REST Framework | Django **5.2.17 LTS** (supported to 2028) + DRF 3.18.0 | Primary business logic + REST API |
| Realtime | Django Channels | latest 4.x | WebSocket consumers, backed by the Redis/Valkey channel layer |
| Async jobs | Celery + Celery Beat | latest 5.x | Thumbnailing, AI calls, search indexing, email, scheduled publishing |
| Database | PostgreSQL | **18** | PG19 is still beta (GA ~Sept 2026) — don't build on a beta |
| Cache / broker | **Valkey** (recommended) or Redis | Valkey 9.1 / Redis 8.x | See licensing note below — pick one deliberately, don't default blindly |
| Search & logs | Elasticsearch + Kibana | **9.5.x** | Content search index + centralized application/system logs |
| Object storage | MinIO, **verify status at setup time** | — | MinIO OSS entered maintenance mode Dec 2025 — see note below |
| Frontend framework | **Nuxt 4** (Nuxt 3 EOLs 2026-07-31) | 4.5.x | SSR-capable app: public site renderer + admin dashboard |
| Node runtime | Node.js | **24 LTS** | Node 26 becomes LTS ~Oct 2026 — reassess then |
| UI kit | Vuetify | 4.x (MD3) or 3.8+ fallback | Confirm `vuetify-nuxt-module` has certified Vuetify 4 support at setup time |
| Styling | TailwindCSS + Sass | latest stable | Utility styling for page-builder output & public site theming |
| State | Pinia | latest 3.x | Frontend state management |
| Utilities | Lodash | latest 4.x | Frontend helpers |
| i18n | `@nuxtjs/i18n` (frontend) + Django i18n + per-content translation tables (backend) | latest | Khmer (`km`) / English (`en`) |
| Containerization | Docker + docker-compose | latest | All services, dev and prod variants |

**⚠️ Django 6.1 vs. 5.2 LTS — resolved during Phase 0 scaffolding:** started on Django 6.1 (the newest release) but `pip install` failed — `django-celery-beat` 2.9.0 caps at `Django<6.1`, so it hasn't caught up to the newest release yet. Settled on **Django 5.2 LTS** instead, which is not a downgrade in any way that matters here: longer support window (through 2028) and wider ecosystem compatibility than chasing the newest annual release. Exactly the kind of thing "latest stable" doesn't account for — a dependency's *transitive* compatibility lags behind its host framework's release.

**🔶 Open Question — Vuetify + Tailwind coexistence:** these two CSS systems can visually collide (Tailwind's preflight reset vs Vuetify's base styles). Recommended default: Vuetify owns the **admin dashboard shell only**; Tailwind (preflight disabled, or scoped/prefixed) is used for **page-builder block components and the public-facing rendered site**, since marketing/landing pages benefit from utility-first flexibility while admin CRUD screens benefit from a consistent component kit. Confirm this split is acceptable. (The glassmorphism/gradient direction in §11 works fine either way — it's implemented with CSS custom properties + `backdrop-filter`, not tied to one library.)

**⚠️ Redis vs. Valkey — real decision, not trivia:** Redis Ltd relicensed Redis off BSD in March 2024 (RSALv2/SSPL — not OSI-approved); Redis 8 added an AGPLv3 tier back in May 2025, so Redis is "open source" again under that license. **Valkey** is the Linux-Foundation-governed, BSD-licensed continuation forked by Redis's original engineers — wire-compatible, production-ready, and the default on AWS ElastiCache/MemoryDB in 2026. For a self-hosted stack like this, **Valkey is the safer default** (permissive license, no ambiguity if you ever redistribute the Docker setup commercially); Redis itself is a fine alternative if you specifically want the Redis brand/tooling. Either works as a drop-in for Celery broker, cache, and Channels layer — pick one and use that name consistently through the compose files, not both.

**⚠️ MinIO status — verify before committing:** as of December 2025 MinIO's open-source Community Edition is in **maintenance mode** (no new features, limited issue review, security fixes only) after admin/console features were progressively moved to the paid edition through 2025. The app only ever talks to storage through the S3 API (via `django-storages`), so this is a low-lock-in decision — MinIO still works fine for pure object storage today, but worth a deliberate choice: (a) stay on MinIO as-is, (b) switch to **OpenMaxIO** (community fork restoring the stripped console, drop-in compatible), or (c) use a more actively-developed S3-compatible alternative (e.g. **Garage**, Apache-2.0). Recommendation: start with MinIO/OpenMaxIO since both are drop-in S3-API compatible with everything else in this spec; revisit only if you hit a wall.

### 2.1 Recommended Complementary Technologies

Beyond the stack you specified, these fill gaps the feature list creates (query performance, SEO, form validation, editing UX). Curated for relevance, not exhaustive — each is a small, isolated addition, none is architecturally load-bearing.

**Backend (Django ecosystem)**

| Library | Purpose | Why it's worth adding here |
|---|---|---|
| `django-environ` | Env-based settings | Keeps secrets/config out of code, standard 12-factor practice |
| `psycopg[binary]` (psycopg3) | Postgres driver | Modern replacement for psycopg2, faster, async-capable |
| `django-redis` / `django-valkey` + `channels-redis` (or valkey equivalent) | Cache + Channels layer backend | The actual packages that make "Redis/Valkey for cache & channel layer" concrete |
| `django-cachalot` | Automatic queryset caching with auto-invalidation on write | Directly targets §6.1 — public pages are read far more than written |
| `django-mptt` or `django-treebeard` | Efficient tree queries | Needed for Page hierarchy, nested Comments, nested Categories — avoids recursive per-row queries |
| `django-simple-history` | Automatic model change history | Does most of §5.10 (Activity Log) for free instead of hand-rolled signals |
| `django-guardian` | Object-level permissions | For edge cases like "Editor can only edit pages they created" — the feature-level permission system in §5.4 doesn't cover per-instance ownership |
| `django-imagekit` or `easy-thumbnails` | Declarative thumbnail/variant pipelines | Reduces custom Celery code for the §5.3 media-optimization pipeline |
| `django-celery-beat` + `flower` | DB-editable periodic tasks + Celery monitoring UI | Needed for scheduled publishing; Flower gives ops visibility into the job queue |
| `django-debug-toolbar` (dev) / `django-silk` (staging) + `nplusone` (CI) | Query/N+1 profiling | Directly enforces the "optimize queries" requirement instead of hoping it holds |
| `django-health-check` | `/health` endpoints per dependency (DB, Redis, ES, MinIO) | Makes the docker-compose healthchecks in §8 real instead of just a TCP port check |
| `sentry-sdk` (optional) | Exception tracking + alerting | Complements ELK — ELK is for logs/search, Sentry is for "page me when this breaks" |

**Frontend (Nuxt ecosystem)**

| Library | Purpose | Why it's worth adding here |
|---|---|---|
| `@nuxtjs/seo` (bundles sitemap, robots, og-image, schema.org) | SEO meta, sitemap.xml, OG images, structured data | This is what actually delivers the "good SEO for public pages" requirement — see §6.3 |
| `@nuxt/image` | Responsive images, lazy loading, format conversion | Frontend half of the media-optimization requirement in §5.3 |
| `@vueuse/core` + `@vueuse/nuxt` | Composable utility library (incl. a ready-made `useWebSocket`) | Saves reinventing common composables; the WebSocket one maps directly onto §5.15 |
| `@pinia/colada` (or `@tanstack/vue-query`) | Server-state cache/dedup layer on top of Pinia | Avoids redundant API calls, directly targets §6.2 frontend performance |
| `vee-validate` + `zod` | Form validation + schema definitions | Every CRUD form (§5.16) needs real validation, not just server-side checks |
| `vuedraggable` (Vue 3 SortableJS wrapper) | Drag/reorder/nest interactions | The actual mechanism behind the §5.2 page builder |
| `@tiptap/vue-3` | Rich text editing | Powers the "Text Section" block's WYSIWYG editing |
| `swiper` (official Vue component) | Carousel/slider | Concrete implementation of the "Swiper" block you named explicitly |
| `@nuxtjs/color-mode` | Light/dark theme switching | Implements the dark-mode feature in §11.8 |
| `@nuxt/fonts` | Auto-downloads and self-hosts Google/custom fonts at build time | No runtime font-CDN request — serves Manrope + Kantumruy Pro (§11.4) from your own origin |
| `@vueuse/motion` | Lightweight animation/micro-interactions | Fits the "modern unique UI" goal without pulling in a heavy animation engine |
| `nuxt-security` | Secure-by-default headers (CSP, HSTS, etc.) | Backs the security non-functional requirement in §6 |
| `@nuxt/test-utils` + `Playwright` | Component + e2e testing | Critical flows (page builder, auth, checkout-style forms) need e2e coverage beyond unit tests |

---

## 3. High-Level Architecture

```
                     ┌─────────────────────┐
                     │   Nuxt 4 Frontend    │
                     │ /admin  → CSR (SPA)  │
                     │ /[...slug] → SSR/ISR │
                     └─────────┬────────────┘
                               │ REST (JWT) + WebSocket
                     ┌─────────▼────────────┐
                     │  Django + DRF API    │
                     │  + Channels (WS)     │
                     └───┬────┬────┬────┬───┘
             ┌───────────┘    │    │    └───────────┐
      ┌──────▼─────┐  ┌───────▼──┐ │  ┌──────────────▼───┐
      │ PostgreSQL │  │  Redis   │ │  │  Celery Workers  │
      │ (primary)  │  │ cache/mq │ │  │ (thumbnails, AI, │
      └────────────┘  │ /channels│ │  │ indexing, email) │
                       └──────────┘ │  └───────┬──────────┘
                     ┌───────────────▼──┐       │
                     │  Elasticsearch   │◄──────┘ (indexing)
                     │  + Kibana        │
                     └──────────────────┘
                     ┌──────────────────┐
                     │      MinIO       │◄── media originals/thumbs
                     └──────────────────┘
```

- Frontend talks to Django only via the REST API and a WebSocket endpoint — never touches Postgres/ES/MinIO directly.
- Media uploads go through Django (auth + validation), which streams to MinIO; Celery generates thumbnails/optimized variants asynchronously and notifies the client over WebSocket when ready.
- Elasticsearch serves two distinct purposes and should use **two separate indices**: (1) content search index (pages/posts) kept in sync via Celery/signals, (2) application log index fed by Django's structured logging output, visualized in Kibana.

---

## 4. Core Domain Model (proposed)

- **User** (custom `AbstractUser`) — locale preference, `theme_preference` (system/light/dark, §11.8), avatar, 2FA enabled flag, `is_superuser` (bypasses all permission checks).
- **Role** — named bundle of permissions (Admin, Editor, User + custom roles). Built on Django's Groups.
- **Permission** — one per feature/action (auto-generated per model: `add_page`, `change_page`, `delete_page`, `publish_page`, `manage_settings`, `moderate_comments`, …). Roles are just permission bundles — nothing hardcoded, so new roles can be composed later.
- **Page** — static/structural content: Landing, About, Contact, Custom, plus the Quiz/Survey/Blog "container" pages. `slug`, `page_type` (FK), `status` (draft/published/scheduled/archived), `parent` (self-FK, for hierarchy like WordPress pages), `comments_enabled`, `created_by`, soft-delete fields, timestamps.
- **PageType** — Landing Page, Blog, About, Contact, Quiz, Survey, Custom… drives which blocks are available and whether specialized data is attached. A page with `page_type=Blog` is the **blog index/archive** — see §5.1, this was the missing piece flagged for recheck.
- **Post** — the actual chronological "blog article" entity (distinct from Page — see §5.1 for why). `slug`, `status`, `category` (FK), `tags` (M2M), `author` (FK User), `featured_image` (FK Media), `published_at`, soft-delete fields, timestamps. Body is block-based via `PostBlock`, exactly like a Page, so the authoring UX is identical for both.
- **Category** — hierarchical (self-FK, like WordPress categories): `name`, `slug`, per-locale translation.
- **Tag** — flat, M2M with Post: `name`, `slug`, per-locale translation.
- **PageTranslation** — per-locale fields for a Page: `title`, `slug`, `body` (where applicable), `meta_title`, `meta_description`, `og_image`, keyed by Page + locale.
- **PostTranslation** — same shape as PageTranslation (keyed by Post + locale), plus `excerpt`.
- **BlockType** — registry entry for a reusable element (Hero, Text Section, Swiper/Carousel, Gallery, CTA Button, Form, Quiz Embed, Survey Embed, Post-List/Blog-Feed, FAQ, Testimonials, Columns/Container, HTML/Custom, …), each with a JSON prop schema + a matching Vue component. Designed as an extensible registry, not a hardcoded enum, so new block types can be added without touching core page logic.
- **ContentBlock (abstract base)** → concrete **PageBlock** / **PostBlock** — ordered/nested instance of a BlockType placed on a Page or a Post, with configured prop values (JSON) and per-locale text overrides. Deliberately **two concrete tables sharing an abstract base, not one generic-FK table** — block content is the single most-read relation in the app (fetched on every public render), and Django's `GenericForeignKey` can't be indexed/joined the way a normal FK can (see §6.1). Comment's Page-or-Post attachment below is the acceptable exception, since comments are fetched far less often and only on demand.
- **Media** — original file + generated variants (thumbnail sizes, optimized web format), dimensions, mime type, size, `uploaded_by`, soft-delete.
- **Comment** — `content_object` (Post or Page, via GenericForeignKey), `author`, `parent` (self-FK for threading), `status` (pending/approved/spam), soft-delete.
- **Setting** — `key`, `value` (JSON), `category`, `is_secret` (encrypted at rest, e.g. AI API keys) — site-wide configuration store.
- **ActivityLog** — `actor`, `verb`, `target_type`/`target_id`, `diff` (before/after JSON), `ip_address`, `timestamp` — audit trail for all mutating actions.
- **AIProviderConfig** — provider name (OpenAI / Anthropic / Gemini / custom OpenAI-compatible endpoint), encrypted API key, optional `base_url` (for the custom-endpoint case), default model, stored via the Settings module.
- **Quiz** / **Question** / **Choice** / **QuizAttempt** / **Answer** — dedicated models with scoring & analytics (confirmed, see §5.1).
- **Survey** / **SurveyQuestion** / **SurveyResponse** — same pattern as Quiz.

All content models (`Page`, `Post`, `Media`, `Comment`, …) share a common `SoftDeleteModel` base (`is_deleted`, `deleted_at`, `deleted_by`, default manager excludes deleted rows, `all_objects` manager for trash views).

---

## 5. Feature Specifications

Every resource below gets the **baseline CRUD contract** defined in §5.16 automatically — this section only calls out what's *extra* per feature.

### 5.1 Content Model: Pages vs. Posts

**This section was missing real logic in the previous draft — flagged and fixed.** The gap: "Page" alone can't cleanly represent a blog. A blog needs chronological ordering, categories/tags, an author byline, and an archive/listing view — none of which make sense on a Contact or Landing page. So, mirroring what WordPress actually does under the hood (and what every modern headless CMS does explicitly), content is split into two entities that **share the same block-based authoring system** so the editing experience feels identical:

**Page** — static, structural, hierarchical content: Landing, About, Contact, Custom pages, plus the "container" pages for Quiz/Survey/Blog. Not part of any chronological feed.
- Created dynamically with a `page_type` (Landing Page, Blog, About, Contact, Quiz, Survey — extensible list).
- Hierarchical (parent/child) like WordPress pages, unique-per-parent slugs.
- Status workflow: draft → published, with optional scheduled publishing (Celery Beat flips status at `publish_at`).
- Extra actions beyond baseline CRUD: `publish`, `unpublish`, `schedule`, `duplicate`, `preview` (unpublished preview link).

**Post** — chronological, taxonomized blog content: the actual articles. This is the piece that needs its own explicit logic:
- Has `category` (one, hierarchical), `tags` (many, flat), `author`, `featured_image`, `excerpt`, `published_at`, and a block-based `body` (same BlockType registry as Pages — a Hero or Gallery block works identically inside a Post).
- Lives at its own canonical URL (e.g. `/blog/<post-slug>`), independent of any Page.
- A Page with `page_type=Blog` is the **index/archive view** for posts — it doesn't contain the articles itself, it contains a **Post-List / Blog-Feed block** (see §5.2's BlockType registry) that queries Posts server-side: paginated, filterable by category/tag, searchable (via Elasticsearch, §5.12), sorted by `published_at`. This mirrors WordPress's "Posts page" concept.
- Extra actions beyond baseline CRUD: `publish`, `unpublish`, `schedule`, `duplicate`, `preview`, plus standard `filter=category`, `filter=tag`, `ordering=-published_at` on the list endpoint.
- **Category** and **Tag** are their own full CRUD resources (admin-manageable, reusable across posts), each with per-locale translation like everything else in §5.14.

**Routing note (concrete, not hand-wavy):** the Nuxt public catch-all route (`/[...slug].vue`) doesn't need to guess whether a URL is a Page or a Post. The backend exposes a single **path-resolver endpoint** — `GET /api/v1/resolve/?path=...` — that looks up the path against both Page and Post slugs and returns `{ type: 'page' | 'post', data: {...} }` (including SEO fields, so SSR can set meta tags before first paint — see §6.3). This keeps frontend routing logic trivial and is the same mechanism WordPress's URL rewrite/permalink resolution conceptually does.

**✅ Confirmed:** Quiz and Survey are full dedicated apps (`quizzes`, `surveys` — see §4) with question/choice models, attempts/responses, scoring rules, and an analytics view, exposed on a Page via an embed block. This is real backend scope, not a lightweight form.

### 5.2 Visual Page Builder & Reusable Elements (Elementor-inspired)
- Admin drags blocks from a palette (Hero, Text Section, Swiper, Gallery, CTA, Form, Columns/Container, Quiz/Survey embed, HTML, …) onto a canvas, reorders/nests them, and edits props in a side panel.
- The **same Vue components** render both the live builder preview and the public page — true WYSIWYG, no drift between editor and output.
- Block registry is extensible: adding a new block type = registering a prop schema + a Vue renderer, no core rewrites.
- Layout blocks (Columns/Container) allow nesting for multi-column layouts.

**✅ Confirmed:** Structured block editor — drag to reorder/nest, configure via the side-panel forms, no freeform absolute positioning. Not a pixel-perfect Elementor clone; optimized for build speed and reliability over maximum visual freedom.

### 5.3 Media Library
- Upload endpoint validates type/size, stores original in MinIO.
- Celery task generates optimized web variant (e.g., WebP) + multiple thumbnail sizes (small/medium/large), stores derived files in MinIO, records dimensions/size/mime.
- Client gets a WebSocket push when processing finishes (so upload UI can swap the spinner for the real thumbnail without polling).
- Extra actions: `regenerate-thumbnails`, usage lookup (which pages reference this file) as a nice-to-have.

### 5.4 Authentication, Roles & Permissions
- Standard email/password auth issuing JWT access + refresh tokens (refresh stored as httpOnly cookie).
- **Superuser** bypasses every permission check (Django's native behavior).
- **Roles** (Admin, Editor, User + custom) are bundles of granular, per-feature permissions — not hardcoded role checks in code. Every feature/action defines its own permission, e.g.:

| Capability | Admin | Editor | User |
|---|---|---|---|
| Manage users & roles | ✅ | ❌ | ❌ |
| Manage settings (incl. AI keys) | ✅ | ❌ | ❌ |
| Create/edit/publish pages | ✅ | ✅ | ❌ |
| Upload media | ✅ | ✅ | ✅ (own only) |
| Moderate comments | ✅ | ✅ | ❌ |
| Post comments | ✅ | ✅ | ✅ |

  *(illustrative default — actual matrix should be configurable via the admin UI, not fixed in code)*

### 5.5 Two-Factor Authentication (2FA)
- TOTP-based (authenticator app) via `django-otp`/`pyotp`, with recovery codes.
- **Opt-in per user**, toggled from account Settings — never forced unless the product owner later decides to require it for certain roles.

### 5.6 Social Login
- `django-allauth` for OAuth: Google and Facebook at launch.
- SPA-friendly flow: social callback → Django issues the same JWT pair used by normal login.

**🔶 Open Question:** Any other providers needed (Apple, Telegram — relevant for a KH/EN audience)?

### 5.7 AI Agent Integration
- Pluggable provider interface (`generate_text`, `translate_text`, and room to add `generate_image`/`summarize` later) with concrete adapters for **all four at launch**: OpenAI, Anthropic (Claude), Google Gemini, and a generic **custom/OpenAI-compatible endpoint** (configurable `base_url` + `api_key` + model name, for self-hosted or other providers).
- User/site supplies their **own API key** per provider in Settings (encrypted at rest, never echoed back in plaintext after save); one provider is selected as active default, switchable per action or globally.
- Surfaced actions: generate content from a prompt, translate a page/post between EN ⇄ KM, suggest SEO meta description.
- AI calls run as Celery tasks (avoid blocking request/response); result delivered over WebSocket to the requesting user's session.

**✅ Confirmed:** four provider adapters ship at launch (OpenAI, Anthropic, Gemini, custom endpoint) — this is more adapter work than a single-provider MVP, but each adapter is a thin, isolated class behind the same interface, so it doesn't block other phases.

### 5.8 Settings Module
- Generic `key → value(JSON)` store, grouped by category (General, Security, AI, Comments, Localization, …), exposed via a dedicated API.
- Secret values (API keys) are encrypted at rest and access-restricted to users with `manage_settings` permission.
- Drives cross-cutting toggles like "2FA available," "default comments-enabled for new pages," "default site locale."

### 5.9 Soft Delete
- Applies to all user-generated content (Page, Post, PageBlock, PostBlock, Media, Comment). Deleting sets `is_deleted`/`deleted_at` instead of removing the row.
- Default manager excludes soft-deleted rows everywhere; a `Trash` view (per resource) lists them with `restore` and (superuser-only) `hard-delete` actions.
- User accounts are **deactivated**, not soft-deleted, to preserve audit/activity-log integrity.

### 5.10 Activity Log / History
- Every mutating action (create/update/delete/restore/publish/login/permission change) is recorded: actor, verb, target, before/after diff, IP, timestamp.
- Exposed as a filterable, searchable API for admins ("who did what, when") — this is a read-heavy audit feed, not user-facing content.

### 5.11 Centralized System Logging (ELK)
- Django structured logging (JSON) shipped to Elasticsearch (directly or via Filebeat/Logstash), visualized in Kibana dashboards.
- Kept in a **separate ES index** from the content-search index in §5.12 — different retention/access needs.
- This is operational/system logging (errors, request logs, worker logs) — distinct from the user-facing Activity Log in §5.10.

### 5.12 Content Search
- Elasticsearch-backed full-text search across pages/posts (title, body, both locales), kept in sync via Celery task or `django-elasticsearch-dsl` signals.
- Powers both the admin "find content" search and (optionally) an on-site search box for visitors.

### 5.13 Comments
- Threaded (self-referential parent), moderation states (pending/approved/spam).
- **Configurable per page** via `Page.comments_enabled`, with a Settings-level default new pages inherit.
- Extra actions beyond baseline CRUD: `approve`, `reject`/`mark-spam`.

**🔶 Open Question:** Must users be logged in to comment, or are guest comments (name/email, no account) allowed?

### 5.14 Localization (Khmer / English)
- Frontend UI strings via `@nuxtjs/i18n` (`en.json`/`km.json`), language switcher.
- Content is bilingual at the data level (§4 `PageTranslation`) — every page/post stores both EN and KM copies, not just the UI chrome.
- AI "translate" action (§5.7) auto-fills the second locale from whichever one the editor wrote first.

**🔶 Open Question:** Is one locale the canonical "source of truth" / fallback when a translation is missing (recommended default: English), or must both always be filled before publishing?

### 5.15 Real-Time (WebSocket) Features
Recommended MVP scope (full collaborative co-editing with conflict resolution is a large separate effort — flagged, not assumed in scope):
- Push notifications (new comment, mention, permission change).
- AI job progress/completion (§5.7).
- Media processing completion (§5.3).
- Basic presence: "Editor X is currently viewing/editing this page."

**🔶 Open Question:** Is real-time **multi-user collaborative editing** (Google-Docs-style, simultaneous edits merging live) actually required, or is presence-awareness + notifications sufficient for v1?

### 5.16 API & CRUD Conventions (applies to every resource)
- DRF ViewSets + routers, versioned under `/api/v1/`.
- **List**: pagination (page/size), `filter` (django-filter FilterSets per resource), `search` (delegates to Elasticsearch where indexed, else DB), `ordering`.
- **Retrieve / Create / Update (PATCH+PUT) / Delete** (= soft delete) / **Restore** as standard.
- **Bulk actions** where useful: bulk delete/restore/publish.
- Consistent error/response envelope; permission-checked per action via the granular permission system in §5.4.
- Auto-generated OpenAPI schema/docs via `drf-spectacular`.

---

## 6. Non-Functional Requirements

- **Security:** DRF throttling on auth/AI endpoints, CORS locked to the Nuxt origin, `nuxt-security` for secure headers (CSP/HSTS), secrets via env vars (never committed), encrypted secret Settings values, input validation at every write endpoint.
- **Testing:** `pytest-django` + `factory_boy` for backend, `Vitest` + `@nuxt/test-utils`/`Playwright` for frontend; each feature area needs at least CRUD + permission-boundary tests.
- **Dev/prod parity:** everything runs via `docker-compose`; a separate prod compose (or later k8s) adds Nginx, proper resource limits, and managed secrets.
- **i18n correctness:** no hardcoded UI strings; all content-bearing models are locale-aware from day one (retrofitting bilingual support later is expensive).

### 6.1 Backend Performance & Query Optimization
- **N+1 is the default failure mode for a page/post/block-heavy app — guard against it explicitly:** `select_related`/`prefetch_related` on every list/detail serializer that traverses relations; `django-debug-toolbar` in dev and `nplusone` in CI so a regression fails the build, not just gets noticed in prod.
- **Index deliberately, not by accident:** unique index on every slug field; indexes on FK columns used in filters (`page_type`, `status`, `category`, `author`); composite index on `(status, published_at)` for the blog-feed query specifically, since that's the hottest read path.
- **Avoid recursive per-row queries on trees:** `django-mptt`/`treebeard` for Page hierarchy, nested Comments, and Category trees — fetch a whole subtree in one query instead of N.
- **Cache the read-heavy paths:** Redis/Valkey via `django-redis`, with `django-cachalot` for automatic queryset caching + auto-invalidation on write. Published Page/Post responses and Settings are the highest-leverage targets — they're read orders of magnitude more than they're written.
- **Search through Elasticsearch, not `ILIKE`:** once content is ES-indexed (§5.12), the `search=` query param should hit ES, not fall back to a Postgres `ILIKE`/trigram scan — that's the whole reason ES is in the stack.
- **Modern driver + connection handling:** `psycopg3` over `psycopg2`; `CONN_MAX_AGE` persistent connections in Django, `pgbouncer` in front of Postgres in prod.
- **Never block the request/response cycle on slow I/O:** thumbnailing, AI calls, search indexing, and email are already async via Celery (§5.3, §5.7) — this is a performance requirement as much as an architectural one.
- **Media never round-trips through Django:** uploads go through Django for auth/validation, but reads should be **presigned URLs straight to MinIO/S3**, not binary proxied through the Django process. Add a CDN in front of object storage in production.
- **Paginate everything** — already required by §5.16, restated here because it's a performance requirement, not just an API convention.

### 6.2 Frontend Performance
- **`@nuxt/image`** for every content image — correct `srcset`, lazy loading, modern formats (WebP/AVIF) — this is the frontend half of the media-optimization requirement in §5.3.
- **Code-split the heavy stuff:** the page-builder editor (drag/drop lib, rich text editor) and admin-only chunks must never ship to a public visitor — lazy-load them behind the `/admin` route boundary.
- **Client-side request caching/dedup** via `@pinia/colada` or TanStack Query — avoid redundant API calls when the same data is needed by multiple components on one screen.
- **Virtualize long lists** in the admin (media library grid, page/post tables at scale) with `vue-virtual-scroller` rather than rendering thousands of DOM nodes.
- **No layout shift:** skeleton loaders instead of spinners-that-cause-reflow, reserved image dimensions.
- **Core Web Vitals as an explicit acceptance bar** for public pages (LCP/INP/CLS) — not just "feels fast," since these are also a direct Google ranking factor, tying performance directly to the SEO goal below.

### 6.3 Rendering Strategy: SSR & SEO

- **Hybrid rendering via Nuxt `routeRules`** (a first-class Nuxt feature, not a workaround): public routes (`/`, `/[...slug]`, `/blog/**`) render with **SSR** (or **prerendered/ISR** for genuinely static pages like About/Contact — best of both cached speed and fresh content); `/admin/**` is explicitly set to `{ ssr: false }` — pure client-rendered SPA behind auth, since it's never indexed and SSR would just add server load for logged-in-only screens with no SEO upside.
- Admin routes additionally get `noindex`/`X-Robots-Tag: noindex` as a belt-and-suspenders measure against accidental indexing.
- **`@nuxtjs/seo`** (sitemap, robots.txt, canonical URLs, Open Graph tags, `schema.org` structured data) driven dynamically from each Page/Post's own `PageTranslation`/`PostTranslation` fields (`meta_title`, `meta_description`, `og_image`) — added to the domain model in §4 specifically to support this.
- Meta tags are set server-side via Nuxt's `useSeoMeta`/`useHead`, populated from the same **path-resolver endpoint** described in §5.1, so the correct title/description/OG image are present in the initial HTML response — not injected client-side after the fact, which defeats the SEO purpose.
- Experimental SSR streaming (available as of Nuxt 4.5) is worth evaluating once the public site is built, for faster time-to-first-byte on content-heavy pages.

---

## 7. Proposed Repository Structure

```
cms/
├─ backend/
│  ├─ config/                  # settings, asgi.py, celery.py
│  ├─ apps/
│  │  ├─ users/                # custom User, auth, 2FA, social login
│  │  ├─ roles_permissions/
│  │  ├─ pages/                # Page, PageType, PageTranslation
│  │  ├─ posts/                 # Post, Category, Tag, PostTranslation
│  │  ├─ blocks/                # BlockType registry, PageBlock, PostBlock
│  │  ├─ media_library/
│  │  ├─ comments/
│  │  ├─ settings_app/          # avoid clashing with Django "settings"
│  │  ├─ activity_log/
│  │  ├─ ai_agent/
│  │  ├─ quizzes/
│  │  ├─ surveys/
│  │  ├─ search/                # Elasticsearch indexing/query layer
│  │  └─ realtime/              # Channels consumers
│  ├─ requirements/
│  └─ Dockerfile
├─ frontend/
│  ├─ pages/
│  │  ├─ admin/                 # dashboard (Vuetify)
│  │  └─ [...slug].vue          # public dynamic page renderer
│  ├─ components/
│  │  ├─ builder/               # drag-and-drop editor
│  │  └─ blocks/                # Hero.vue, Swiper.vue, TextSection.vue ... (shared builder+public)
│  ├─ stores/                   # Pinia
│  ├─ composables/
│  ├─ locales/                  # en.json, km.json
│  └─ Dockerfile
├─ infra/
│  ├─ docker-compose.yml
│  ├─ docker-compose.prod.yml
│  ├─ nginx/
│  └─ elk/
└─ docs/
```

---

## 8. Docker Compose Service Layout

`backend` (Django/Daphne, ASGI for Channels) · `celery-worker` · `celery-beat` · `frontend` (Nuxt) · `postgres` · `redis` · `elasticsearch` · `kibana` · `minio` · `nginx` (prod reverse proxy). Dev compose mounts source as volumes for hot-reload; prod compose builds immutable images.

---

## 9. Recommended Build Phases

This scope is too large to build as one unit — sequence it so each phase produces something runnable:

0. **Infra skeleton** — docker-compose brings up every service as an empty shell with health checks; Django + Nuxt projects scaffolded and talking to each other.
1. **Identity foundation** — custom User, Roles/Permissions, Settings module, JWT auth, superuser.
2. **Core content (no builder yet)** — Page/PageType/PageTranslation **and** Post/Category/Tag/PostTranslation models, plain CRUD admin screens, the path-resolver endpoint (§5.1).
3. **Media library** — MinIO integration, upload, async thumbnailing/optimization.
4. **Visual page builder** — Block registry, drag/drop canvas, shared-component WYSIWYG, public renderer.
5. **Cross-cutting concerns** — soft delete, activity log, comments (now that core models exist).
6. **Search** — Elasticsearch content indexing + search UI.
7. **AI agent integration** — Settings-driven API keys, generation/translation actions, async + WebSocket delivery.
8. **Real-time** — notifications, presence, live activity feed via Channels.
9. **Auth hardening** — 2FA, social login.
10. **Observability & polish** — centralized ELK logging/Kibana dashboards, test coverage, docs.

---

## 10. Decisions

### 10.1 Confirmed by product owner (2026-08-12)
1. **Single-tenant, single-site CMS** — not multi-site/multi-tenant like WordPress Multisite.
2. **Page builder = structured block editor** — drag/reorder/nest with form-based config, not freeform absolute positioning.
3. **Quiz/Survey are dedicated backend apps** with scoring/attempts/analytics, exposed on a page via an embed block.
4. **AI agent ships with 4 provider adapters at launch**: OpenAI, Anthropic, Gemini, and a generic custom/OpenAI-compatible endpoint. User supplies their own key(s) in Settings.

### 10.2 Still-open assumptions (reasonable defaults in use, not yet explicitly confirmed)
1. JWT auth (access + httpOnly-cookie refresh) for the SPA.
2. Comments require a logged-in account (no anonymous/guest comments) — §5.13.
3. English is the fallback/default locale when a Khmer translation is missing — §5.14.
4. WebSocket scope for v1 = notifications + job progress + presence — **not** simultaneous multi-user co-editing — §5.15.
5. Vuetify scoped to the admin shell, Tailwind to page-builder/public output — §2.
6. Only Google + Facebook social login at launch (no Apple/Telegram) — §5.6.
7. Monorepo with `/backend` + `/frontend`.

---

## 11. UI Design System — "Ember"

**Live preview: [Ember — CMS Visual Direction](https://claude.ai/code/artifact/ea5a6776-a083-426d-9a39-7ddabb6a404a)** — rendered swatches, gradients, glass material, Vuetify-themed component mockups (§11.7), and real embedded typography (§11.4), all switchable between light/dark (§11.8) in the page itself. What follows is the written spec behind that preview.

Direction: **glassmorphism + gradient, warm rather than the generic cool blue-purple most AI/SaaS products default to.** Frosted-glass panels floating over a coral→wine gradient world, generous rounded corners, soft tinted shadows instead of flat Material-default drop-shadows. Applies to both the admin dashboard (Vuetify) and the public site (Tailwind) from **one shared token source** (§11.6), so the two halves never visually drift apart.

### 11.1 Color Palette
| Token | Hex | Use |
|---|---|---|
| Ember (primary) | `#FF6B4A` | Primary buttons, links, focus rings, active states |
| Wine (gradient partner) | `#B0296B` | Deep accents, glass-shadow tint, gradient end-stop |
| Gold (tertiary) | `#E3B23C` | Used sparingly — draft/warning state, small highlights |
| Ink (neutral, dark) | `#14111C` | Dark-mode background, light-mode text |
| Cream (neutral, light) | `#FBF7F2` | Light-mode background — warm-tinted, deliberately not stock white |
| Info (the one cool note) | `#3873D9` | Informational states only — kept separate so it stays meaningful |

Plus semantic status colors (success `#2F9D68`, error `#D93636`, gold doubling as warning) — kept visually distinct from the brand accent so state is legible at a glance in status chips (Published/Draft/Pending/Trashed), independent of theme.

### 11.2 Glassmorphism Rules
- `backdrop-filter: blur(1.25rem) saturate(160%)` on glass panels (`-webkit-` prefix for Safari); never stack more than two blurred layers.
- Always a visible `0.0625rem` (1px) translucent border — unbordered blur reads as "blurry," not "glass."
- Soft, tinted shadows, not pure black: e.g. `0 0.5rem 2rem rgba(176,41,107,0.16)`.
- Glass panels sit on a gradient or busy ground, never a flat single color — that contrast is what sells the material.

### 11.3 Gradient Usage
- Signature gradient: `linear-gradient(135deg, #FF6B4A 0%, #B0296B 100%)` — hero backgrounds, primary CTA buttons, login screen, active/selected states in the page builder.
- Used deliberately, not everywhere — body text areas, data tables, and form fields stay flat so the gradient keeps its impact.

### 11.4 Typography
- **UI/body (Latin): Manrope.** Confirmed and embedded in the live preview — variable font (one file, weights 300–800), distinctive without being a novelty face.
- **Khmer: Kantumruy Pro, not Noto Sans Khmer.** Noto Sans Khmer is the generic default every project reaches for — its x-height and weight don't match most modern Latin sans faces, which is exactly why the first version of the preview "looked off" next to the system Latin stack. Kantumruy Pro is Google's newer, purpose-built Khmer UI family, designed to sit visually closer to contemporary Latin type. Applied via `:lang(km) { font-family: 'Kantumruy Pro', 'Manrope', system-ui, sans-serif; }`.
- **Self-host both in the real app** via the `@nuxt/fonts` module (auto-downloads and self-hosts Google Fonts at Nuxt build time — no runtime request to Google's CDN, no font-swap layout shift, no third-party request for a KH/EN audience where CDN latency/availability can vary). The live preview embeds both fonts directly as base64 `@font-face` data for the same underlying reason — Artifacts can't reach a font CDN either.
- Headline moments use the gradient-fill technique (`background: var(--gradient-primary); background-clip: text;`) rather than a third typeface — carries the "unique" feeling without another font to load.

### 11.5 Shape, Elevation & Units
Border radius scale: `--radius-sm: 0.5rem` (inputs, chips) · `--radius-md: 0.875rem` (cards) · `--radius-lg: 1.25rem` (panels) · `--radius-xl: 1.75rem` (hero/modal) · `--radius-full: 999rem` (pills/avatars — any value larger than the element always fully rounds it, so the exact number doesn't matter). Elevation via soft tinted shadows + blur, not flat Material-style drop-shadow steps.

**Units: rem everywhere, px only for `@media` breakpoints.** Every size — font-size, padding, margin, gap, border-radius, border-width, shadow offsets, blur radius — is `rem` (1rem = 16px base), so the UI scales correctly when a user changes their browser's base font size, which is an accessibility requirement, not a style preference. The one deliberate exception is responsive breakpoints (e.g. `@media (max-width: 640px)`), which stay in `px` per normal CSS convention — viewport breakpoints describe physical screen size, not text zoom, so they shouldn't move when a user's font-size preference does.

### 11.6 Implementation note (ties back to §2's Vuetify/Tailwind split)
Define all tokens above once — CSS custom properties or a shared `design-tokens.json` — then point **both** Vuetify's theme config (`colors`, component `defaults` for border-radius) **and** Tailwind's `theme.extend` at the same source. One source of truth means the admin dashboard, the public site, and the page-builder's live preview (which renders the same block components in both places) never drift apart visually.

### 11.7 Vuetify Theme Mapping

Concrete wiring, not just "point Vuetify at the tokens":

```ts
// vuetify.config.ts
import { createVuetify } from 'vuetify'
import { tokens } from './design-tokens' // same source Tailwind reads from, §11.6

export default createVuetify({
  theme: {
    defaultTheme: 'emberLight', // overridden at runtime by the dark-mode toggle, §11.8
    themes: {
      emberLight: {
        dark: false,
        colors: {
          primary: tokens.light.ember,
          secondary: tokens.light.wine,
          tertiary: tokens.light.gold,
          background: tokens.light.bg,
          surface: tokens.light.surface,
          error: tokens.light.error,
          success: tokens.light.success,
          info: tokens.light.info,
          warning: tokens.light.gold,
        },
      },
      emberDark: {
        dark: true,
        colors: {
          primary: tokens.dark.ember,
          secondary: tokens.dark.wine,
          tertiary: tokens.dark.gold,
          background: tokens.dark.bg,
          surface: tokens.dark.surface,
          error: tokens.dark.error,
          success: tokens.dark.success,
          info: tokens.dark.info,
          warning: tokens.dark.gold,
        },
      },
    },
  },
  defaults: {
    VCard: { rounded: 'md' },
    VBtn: { rounded: 'sm' },
    VTextField: { variant: 'outlined', rounded: 'sm' },
    VChip: { rounded: 'pill' },
    VAppBar: { elevation: 0, class: 'ember-glass-appbar' }, // glass treatment — see below
  },
})
```

- Vuetify's built-in `rounded` scale (`0, sm, md, lg, xl, pill`) is remapped once, globally, to §11.5's rem values — rather than overriding border-radius component-by-component.
- Glassmorphism on the app bar isn't a native Vuetify theme property, so it's applied via one global class hooked through `defaults.VAppBar.class`: `.ember-glass-appbar { background: var(--glass-bg); backdrop-filter: blur(1.25rem) saturate(160%); border-bottom: 0.0625rem solid var(--glass-border); }`. Same pattern for any other component that needs glass treatment Vuetify doesn't support out of the box.
- The live preview's "Applied to Vuetify" section shows the result: elevated / tonal / outlined `VCard` and `VBtn`, an outlined `VTextField`, a `VSwitch`, and a glass `VAppBar` over a nav rail — themed mockups of the real components, built from these exact tokens.

### 11.8 Dark Mode

A real, user-facing feature — not just a token exercise. Three states, matching the toggle already in the live preview:
- **System** (default) — follows the OS/browser's `prefers-color-scheme`.
- **Light** / **Dark** — explicit user override, persisted.

Implementation:
- Frontend: `@nuxtjs/color-mode` (§2.1) manages the three-state toggle and persists the choice in `localStorage` for anonymous public-site visitors.
- Logged-in users: the preference additionally syncs to `User.theme_preference` (§4) via a lightweight PATCH on change, so it follows them across devices.
- Both halves of the app flip together from one source: the Vuetify admin shell switches its active theme (`emberLight`/`emberDark`, §11.7) and the Tailwind public site flips the same CSS custom properties via `[data-theme]` — one toggle, one token set, nothing drifts.
- Applies inside the page-builder's live preview canvas too, so an editor can check how a page reads in both modes before publishing.

---
