# Codex7 Delivery Guide

The Vinted repo contains scraper logic but no deployed service or UI yet. Codex7’s goal is to deliver both the FastAPI backend and a shadcn/ui-powered frontend with MCP assistance.

## Target Repository Layout
- `app/`: Existing Python scraper, ingestion utilities, and shared domain code.
- `fastAPI/`: FastAPI service skeleton ready for endpoint implementations.
- `frontend/`: New React/Next.js (or Vite) project to host the dashboard (currently empty).
- `WEBUI_README.md`: Product brief for dashboard, listings explorer, configuration editor, cron management.
- `migrations/`, `test/`, `test_*.py`: Supporting artifacts for the scraper code.

## Current Status
- `fastAPI/` exposes working endpoints for stats, listings, configs (including `/run` + `/status`), taxonomy, and cron management.
- Redis integration (`REDIS_URL` in `.env`) stores runtime scrape status and publishes updates for the frontend.
- Database dependency wiring reuses the async engine defined in `app.db.session`.
- Environment variables from the repository `.env` file are loaded automatically when the FastAPI app starts.
- `frontend/` delivers a TypeScript Next.js 15 UI (Tailwind + shadcn/ui) with dashboard metrics, listings explorer, and a scrape-config manager (CRUD + manual run + status polling via Redis).
- `test/test_fastapi_api.py` covers stats, listings, and config APIs against a temporary SQLite database with mocked Redis/scraper integrations.

## Database Snapshot
- `listings`: core catalogue data (pricing fields, status flags, seller metadata, category/platform IDs, timestamps).
- `price_history`: time-series price data linked to listings via `listing_id`.
- `scrape_configs`: user-defined scrape jobs (query params, cron schedule, run statistics).

## Backend Requirements (`fastAPI/`)
- Stand up a FastAPI service exposing endpoints aligned with the UX spec in `WEBUI_README.md`.
- Planned routes:
  - `GET /api/stats` for dashboard metrics.
  - `GET /api/listings` and `GET /api/listings/{id}` with pagination, search, and price history.
  - CRUD endpoints under `/api/configs`, plus `POST /api/configs/{id}/run`.
  - `GET /api/categories`, `GET /api/platforms` for taxonomy.
  - `GET /api/cron/jobs`, `POST /api/cron/sync` for scheduling.
- Wire these handlers to the scraper/data layer under `app/` (import models, DB helpers, scheduler utilities). If interfaces are missing, extend `app/` instead of duplicating logic inside `fastAPI/`.

## Frontend Mission (`frontend/`)
1. Ask Codex7 (shadncui) MCP to scaffold a Next.js or Vite + React project with shadcn/ui styling.
2. Implement the four feature areas spelled out in `WEBUI_README.md`:
   - Dashboard cards fed by `/api/stats`.
   - Listings table with filters, pagination, price trend indicators.
   - Scrape configuration CRUD flow with optimistic updates.
   - Cron job list + manual sync control.
3. Produce static assets (e.g., `npm run build && npm run export` or Vite’s `dist/`) consumable by the FastAPI service.

## Codex7 MCP Setup
- `.mcp.json` should already declare the `codex7-shadncui` server; verify the entry rather than re-adding it.
- Confirm `.claude/settings.json` allows `mcp__codex7-shadncui__*` commands.
- Ensure `OPENAI_API_KEY` (or alternative Codex7-compatible model key) is present in the environment used by MCP.

## Execution Gameplan
1. Harden the new FastAPI service with automated tests and richer Redis status payloads (pagination progress, error details).
2. Install shadcn/ui inside `frontend/`, scaffold design system primitives, and implement the dashboard, listings browser, config editor, and cron view against the live API.
3. Wire the frontend to poll `/api/configs/{id}/status` (and optionally subscribe to the `config_status` Redis channel for realtime updates).
4. Decide how FastAPI will serve the frontend build output (mount `StaticFiles` once the Next.js export path is known) and document the deployment workflow.

## Validation Checklist
- Repository contains the three top-level directories: `app/`, `fastAPI/`, `frontend/`.
- FastAPI service responds with expected payloads for all planned routes (manual or automated tests).
- Frontend consumes those APIs, surfaces form validation/errors, and matches the UX flows from `WEBUI_README.md`.
- Production build artifacts exist and can be hosted by the FastAPI service (verify locally with uvicorn once ready).
- Error paths (cron sync failure, scraper run failure, empty listings) surface helpful UI feedback.

Track work in version control and coordinate major contract changes between `app/`, `fastAPI/`, and `frontend/`. When in doubt, reference domain logic in `app/` and existing tests to keep behaviour consistent.
