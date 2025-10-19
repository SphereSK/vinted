# Repository Guidelines

## Project Structure & Module Organization
- `app/cli.py` exposes the Typer-powered `vinted-scraper` CLI; subpackages under `app/` hold API (`app/api`), database (`app/db`), scraping, utilities, and scheduling logic.
- `app/api/main.py` runs the FastAPI service, mounts the Vue frontend, and orchestrates async DB access via SQLAlchemy sessions in `app/db`.
- `app/scraper/` contains HTML parsers, session warmup, and catalog helpers that feed the ingest pipeline in `app/ingest.py`.
- `migrations/` stores raw SQL changes; run them manually when schema updates are required.
- `frontend/index.html` ships the lightweight dashboard served from the API root; static assets live alongside it.
- Top-level `debug_*.py` scripts and the `test/` directory provide ad-hoc probes for catalog, filters, and request behavior.

## Build, Test, and Development Commands
```bash
pip install -e .                               # Install editable package with Python deps
uvicorn app.api.main:app --reload              # Start API + serve frontend at http://localhost:8000
vinted-scraper scrape --search-text "ps5" --max-pages 2 --delay 1.0  # Run a sample scrape
python -m app.scheduler list                   # Inspect cron jobs synced from scrape configs
python test/test_requests.py                   # Smoke-check live HTTP headers against Vinted
```
Use `start_server.sh` if you prefer the convenience wrapper around the API launch.

## Coding Style & Naming Conventions
- Target Python 3.10+ with 4-space indentation, type hints, and concise docstrings that explain intent rather than mechanics.
- Follow module and function `snake_case`, class `PascalCase`, and constant `UPPER_SNAKE_CASE` conventions visible across `app/`.
- Keep async flows non-blocking; long-running or I/O-heavy logic should remain inside `async` functions mirroring `app/ingest.py`.
- Preserve SQLAlchemy model formatting: one column per line, explicit `Mapped[...]` annotations, and schema-aware constraints.

## Testing Guidelines
- Formal pytest coverage is not yet in place; rely on targeted scripts under `test/` and root-level `test_*.py` to validate network behavior, parsing, and shipping calculations.
- When adding new features, mirror those scripts with minimal, deterministic repro steps and prefer isolating network-facing code behind injectable clients for future pytest integration.
- Document any live credentials or throttling expectations in the PR to help reviewers reproduce results without triggering rate limits.

## Commit & Pull Request Guidelines
- Follow the existing Conventional Commit style (`feat:`, `fix:`, etc.) with concise, present-tense summaries (e.g., `feat: add category search command`).
- Scope one logical change per commit, referencing issues where applicable.
- Pull requests should outline motivation, implementation notes, manual test results (commands run and outcomes), and any schema or `.env` changes; include dashboard screenshots when UI changes touch `frontend/`.
- Update relevant docs (`HELP_REFERENCE.md`, `PROJECT_SUMMARY.md`, or new CLI help) whenever a CLI flag, API response, or schema changes to keep the documentation set coherent.

## Security & Configuration Tips
- Copy `.env.example` to `.env`, fill database credentials, and never commit sensitive values or generated `cookies*` artifacts.
- Respect the default `settings.request_delay` and pagination limits to avoid anti-bot triggers; document deviations when experiments require faster scraping.
- When syncing cron jobs, confirm the generated absolute paths in `app/scheduler.py` still match your deployment location before writing to the system crontab.
