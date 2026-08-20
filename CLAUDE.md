# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Django backend ("MoreFunctionsForGLPI") that extends a GLPI (IT asset/ticketing) instance with features GLPI doesn't provide natively: a live NOC-style ticket dashboard, a label-printing subsystem, technical disposal/repair report generation, GLPI SSO into Django admin, and webhook-driven automation that pushes status changes back into GLPI. It is designed to run embedded in an iframe inside GLPI itself, and can also be packaged as a standalone Windows executable.

## Commands

Run from the repo root, with the venv active (`venv/` exists locally; `manage.py`/`run.py` assume `core.settings` as `DJANGO_SETTINGS_MODULE`).

```bash
python manage.py runserver          # dev server (ASGI/Channels-aware via daphne when using run.py/waitress in prod)
python manage.py migrate
python manage.py makemigrations <app_label>
python manage.py createsuperuser
python manage.py collectstatic
```

Note: migration files are version-controlled (`apps/*/migrations/*.py`). Do not hand-edit committed migrations; run `makemigrations` and commit the generated file like any other source change. Existing deployments that predate this (each environment had generated its own local, uncommitted migration history) were reconciled by adopting this repo's migration files as canonical and fake-applying them (`migrate <app> --fake`) wherever the target schema already matched — see git history around the `dev` branch's migrations commit for the reconciliation notes per app.

Config comes from a `.env` file (see `.envexample`) loaded via `python-dotenv`: `SECRET_KEY`, `DB_ENCRYPTION_KEY` (Fernet key, required — used to encrypt stored DB/API credentials), `MYSQLDB_*`, `BASE_URL`, `CSRF_TRUSTED_ORIGINS`, `CSP_FRAME_ANCESTORS`, `CORS_ALLOWED_ORIGINS`, `REDIS_HOST`/`REDIS_PORT` (required — Channels layer is Redis-backed, no in-memory fallback is wired up).

### Standalone executable build

`run.py` is the PyInstaller entrypoint (not `manage.py`): it wraps Django with `waitress` on port 8000 and has a `postinstall` mode (`python run.py postinstall`) that generates `.env`, runs migrations, and creates a default `admin/password` superuser. `DirectLabelPrinter.spec` builds the exe (`pyinstaller DirectLabelPrinter.spec`). This packaging exists so the label-printer app can be deployed as a Windows service/executable independent of a full server deployment.

### Vue dashboard frontend

The NOC dashboard's frontend lives separately at `apps/panel/frontend/vue/` (Vue 3 + Vite + Tailwind 4 + TypeScript, package manager pnpm):

```bash
cd apps/panel/frontend/vue
pnpm dev        # vite dev server on :3000
pnpm build      # vite build + esbuild server bundle to dist/
pnpm check      # tsc --noEmit
pnpm format     # prettier --write .
```

It talks to the Django backend over the `/glpi/api/...` REST endpoints and a `ws/panel/` WebSocket; CORS/CSRF for this origin must be present in `CORS_ALLOWED_ORIGINS`/`CSRF_TRUSTED_ORIGINS`.

## Architecture

### App layout (`apps/`)

- **`dbcom`** — the integration core. Not a user-facing app; provides `db_manager.Database`, a raw-MySQL query wrapper (via `mysql-connector-python`, dict cursors, context-managed transactions), configured per-connection through the `ExternalDbConfig` model (credentials stored Fernet-encrypted, decrypted on read). `glpi_queries.py` (500+ lines) holds hand-written SQL against **GLPI's own database schema** (`glpi_tickets`, `glpi_entities`, etc.) — this is how ticket/dashboard data is read, bypassing the GLPI REST API entirely for performance. Writes back to GLPI (status changes) instead go through the **legacy GLPI API v1** (`initSession`/`killSession` token flow, `utils.py`) because the v1 API supports the item-status mutations needed; `GLPIConfig` is a singleton model holding the v2 API URL/tokens. `GLPIWebhookView` (wired in `core/urls.py`) receives GLPI webhooks and applies `AutomationRule`s (category → status mapping) to drive `change_glpi_items_status`.
- **`glpiintegrator`** — SSO bridge: `glpi_sso` view logs a Django user in from an HMAC-SHA256-signed, base64 payload (`payload`+`sig` query params, 5-minute timestamp tolerance) issued by GLPI, auto-creating/linking a `GlpiProfile` (GLPI user id ↔ Django `User`). Also owns `AllowAdminInIframeMiddleware`, which strips `X-Frame-Options` and sets `Content-Security-Policy: frame-ancestors <CSP_FRAME_ANCESTORS>` so the Django admin can be embedded inside GLPI's UI.
- **`panel`** — the live NOC dashboard backend. `PanelConsumer` (Channels `AsyncWebsocketConsumer`, mounted at `ws/panel/`) pushes ticket/KPI/project data pulled from `dbcom.glpi_queries` on a poll loop whose interval comes from the singleton `DashboardSettings` model; also tracks connected `Display` clients (by `channel_name`) so `display_control` group messages can remote-switch a kiosk's screen. Its own REST endpoints live under `glpi/api/...` (`apps/panel/urls.py`). Frontend is the separate Vue app described above.
- **`printer`** — label printing. `PrintServer` model holds connection details (incl. Fernet-encrypted API key) for an **external** print microservice reached over HTTP (`X-API-Key` header); `EtiquetaLayout` stores a JSON-defined label layout (`layout_json`) rendered dynamically with ReportLab + a registered custom TTF font. `services.py` builds the PDF from a layout + data and POSTs it to the print server. All endpoints under `/api/...` require **JWT auth** (`djangorestframework-simplejwt`; see `JWT_AUTHENTICATION.md` for the token endpoints and usage) — this is the one subsystem with token-based API auth; the rest of the project relies on Django session auth.
- **`reports`** — generates formal PDF documents (likely via WeasyPrint, in requirements) for asset lifecycle events: `LaudoBaixa`/`ItemLaudo` (disposal reports) and `ProtocoloReparo`/`ItemReparo` (repair protocols), both copying denormalized snapshots of GLPI asset data at creation time rather than referencing GLPI live. Both parent models auto-generate sequential document numbers on save (`LT-<year>-<seq>`, `PRE-<year>-<seq>`) and use Django proxy models purely to get a friendlier label in the admin menu. `ProtocoloReparo` has a `FINALIZADO` status that locks the record (raises `ValidationError` on further edits/deletes once finalized). `ConfiguracaoCabecalho` is a singleton holding company letterhead info for report headers.

### Cross-cutting patterns

- **Singleton models**: `GLPIConfig`, `DashboardSettings`, `ConfiguracaoCabecalho` all force `pk=1` in `save()` and no-op `delete()` — treat these as global config, not per-row data.
- **Encrypted-at-rest fields**: any model with a `password`/`api_key` field (`ExternalDbConfig`, `PrintServer`) encrypts via `cryptography.fernet.Fernet(settings.DB_ENCRYPTION_KEY)` in `save()`/a `set_*` method, with a paired `get_decrypted_*()` accessor — never read `.password`/`.api_key` directly for use, always go through the decrypt accessor.
- **Two GLPI integration paths**: direct MySQL reads (`dbcom.glpi_queries`) for anything read-heavy/reporting, versus the legacy GLPI REST API v1 session flow (`dbcom.utils`) for anything that needs to *write* into GLPI. When adding a GLPI-touching feature, follow whichever pattern matches read vs. write.
- **ASGI split**: `core/asgi.py` routes HTTP through standard Django and WebSocket through Channels' `URLRouter` (currently only `apps.panel.routing.websocket_urlpatterns`); `CHANNEL_LAYERS` requires Redis in all environments (no in-memory dev fallback configured).
- Language/locale: UI-facing strings, model verbose names, and comments throughout the codebase are in Portuguese (pt-br); `TIME_ZONE` is `America/Porto_Velho`.
