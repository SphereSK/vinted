# FastAPI Service Skeleton

This directory hosts the future FastAPI application that will expose the scraper and scheduler capabilities described in `WEBUI_README.md`.

## Current State
- `main.py` bootstraps the FastAPI instance, registers the stats/listings/configs/taxonomy/cron routers, enables permissive CORS, and loads `.env` settings (including the DB URL).
- `routers/` now exposes functional endpoints backed by the shared SQLAlchemy models:
  - `/api/stats`, `/api/listings`, `/api/listings/{id}`
  - `/api/configs` CRUD, `/api/configs/{id}/run`, `/api/configs/{id}/status`
  - `/api/categories`, `/api/platforms`
  - `/api/cron/jobs`, `/api/cron/sync`, `/api/cron/build`
- `services/scraper.py` coordinates background scrape runs and updates runtime state.
- `redis.py` provides a shared Redis connection for frontend/backend coordination (status updates published to `config_status`).
- `dependencies.py` reuses the existing async DB engine defined in `app.db.session`.

## Next Steps
1. Flesh out automated tests for the new routers and scraper service (e.g., with a test database and mocked redis).
2. Expand runtime status data if additional progress metrics are needed for the UI (e.g., per-page updates).
3. Configure FastAPI to serve the frontend build artifacts once the Next.js app is ready (e.g., mount `StaticFiles` to the exported directory).

## Testing
- `test/test_fastapi_api.py` exercises the stats, listings, and config endpoints with an in-memory SQLite database and mocked Redis/scraper orchestration.
- Run `pytest test/test_fastapi_api.py` from the repository root. The fixture patches `app.db.session` to avoid touching production credentials.

Run the service locally once endpoints are implemented:

```bash
uvicorn fastAPI.main:app --reload
```

The application loads environment variables from the repository-level `.env`, so ensure `DATABASE_URL` and `REDIS_URL` are correctly set before launching uvicorn.

### Scheduler configuration
- `SCRAPER_WORKDIR` (default: project root) controls the `cd` prefix used when building cron commands.
- `SCRAPER_COMMAND` overrides the executable used by cron jobs. By default it runs `python -m app.cli scrape` using the same interpreter that loaded the API, so no extra PATH juggling is required. Set `SCRAPER_PYTHON` if the scraper should execute under a different interpreter.
- `SCRAPER_USE_PROXY` (default: `false`) toggles whether `--no-proxy` is appended to generated commands.
- `SCRAPER_CRON_COMMENT` (default: `vinted-scraper`) prefixes cron job comments so they can be listed/removed via the API.
- `/api/cron/build` accepts a payload mirroring scrape parameters and returns the exact command string cron would execute, plus the optional schedule supplied by the caller. Manual scrapes triggered via `/api/configs/{id}/run` reuse the same command builder under the hood, execute it asynchronously, and publish progress through Redis (`config_status`) and the `last_run_*` metadata fields.
- Scrape configs accept an optional `extra_args` list; any entries are appended to the generated CLI command when cron jobs are synced.
- Scrape configs expose the same knobs as the CLI (`order`, `extra`/-e filters, `--locale`, `--details-for-new-only`, `--error-wait`, `--max-retries`, `--base-url`, `--details-strategy`, `--details-concurrency`, proxy toggle), and `/api/cron/build` mirrors those fields when composing commands.
- `SCRAPER_EXTRA_ARG_MAX_LENGTH` (default: `128`) limits the length of each extra CLI token; allowed characters include alphanumerics plus `. _ - : @ % + = / , [ ] & ?`.
- `healthcheck_ping_url` (per config) automatically pings Healthchecks.io: the base URL is contacted on success and `/fail` on errors. Global tuning knobs include `SCRAPER_HEALTHCHECK_TIMEOUT` (seconds, default `10`) and `SCRAPER_HEALTHCHECK_RETRIES` (default `3`).

## Authentication
- Set `FASTAPI_API_KEY` in `.env` to require a static API key for all `/api/*` endpoints (header name defaults to `X-API-Key`).
- Override the header name via `FASTAPI_API_KEY_HEADER` if your deployment needs a different header.
- If `FASTAPI_API_KEY` is unset or empty, the API remains open while `/` health and docs endpoints stay publicly accessible.
