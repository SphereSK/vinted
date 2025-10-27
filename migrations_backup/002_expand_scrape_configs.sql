-- Migration: expand scrape_configs with scheduler/CLI options
-- ------------------------------------------------------------------
-- This script targets Postgres. If you are using a different schema
-- name, replace "vinted" below with your schema before executing.
--
--   psql "$DATABASE_URL" -f migrations/002_expand_scrape_configs.sql
--
-- For SQLite development databases, run the ALTER TABLE statements
-- (without schema qualifiers) manually using the sqlite3 CLI.

ALTER TABLE IF EXISTS vinted.scrape_configs
    ADD COLUMN IF NOT EXISTS extra_filters JSONB,
    ADD COLUMN IF NOT EXISTS locales JSONB,
    ADD COLUMN IF NOT EXISTS "order" VARCHAR(64),
    ADD COLUMN IF NOT EXISTS details_for_new_only BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS use_proxy BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS extra_args JSONB,
    ADD COLUMN IF NOT EXISTS error_wait_minutes INTEGER DEFAULT 30,
    ADD COLUMN IF NOT EXISTS max_retries INTEGER DEFAULT 3,
    ADD COLUMN IF NOT EXISTS base_url VARCHAR(512),
    ADD COLUMN IF NOT EXISTS details_strategy VARCHAR(32) DEFAULT 'browser',
    ADD COLUMN IF NOT EXISTS details_concurrency INTEGER DEFAULT 2;

-- Backfill NULL values to honour the CLI defaults.
UPDATE vinted.scrape_configs
SET
    details_for_new_only = COALESCE(details_for_new_only, FALSE),
    use_proxy = COALESCE(use_proxy, TRUE),
    error_wait_minutes = COALESCE(error_wait_minutes, 30),
    max_retries = COALESCE(max_retries, 3),
    details_strategy = COALESCE(details_strategy, 'browser'),
    details_concurrency = COALESCE(details_concurrency, 2);
