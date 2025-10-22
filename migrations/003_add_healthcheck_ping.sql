-- Migration: add optional healthcheck ping URL to scrape_configs
-- ------------------------------------------------------------------
-- Apply against Postgres (adjust schema if different from default "vinted").
--   psql "$DATABASE_URL" -f migrations/003_add_healthcheck_ping.sql
-- For SQLite, run the ALTER TABLE statement manually without the schema prefix.

ALTER TABLE IF EXISTS vinted.scrape_configs
    ADD COLUMN IF NOT EXISTS healthcheck_ping_url VARCHAR(512);

-- No backfill required; NULL indicates healthchecks are disabled for the config.
