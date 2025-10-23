-- Migration: taxonomy master data tables
-- ------------------------------------------------------------------
-- Creates canonical lookup tables for categories, platforms, conditions,
-- and listing sources. Populate them using the application seeding logic
-- or insert rows manually as needed.

CREATE TABLE IF NOT EXISTS vinted.category_options (
    id INTEGER PRIMARY KEY,
    name VARCHAR(128) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS vinted.platform_options (
    id INTEGER PRIMARY KEY,
    name VARCHAR(128) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS vinted.condition_options (
    code VARCHAR(64) PRIMARY KEY,
    label VARCHAR(128) NOT NULL
);

CREATE TABLE IF NOT EXISTS vinted.source_options (
    code VARCHAR(64) PRIMARY KEY,
    label VARCHAR(128) NOT NULL
);

-- SQLite variant (uncomment when applying to sqlite databases)
-- CREATE TABLE IF NOT EXISTS category_options (
--     id INTEGER PRIMARY KEY,
--     name TEXT NOT NULL UNIQUE
-- );
-- CREATE TABLE IF NOT EXISTS platform_options (
--     id INTEGER PRIMARY KEY,
--     name TEXT NOT NULL UNIQUE
-- );
-- CREATE TABLE IF NOT EXISTS condition_options (
--     code TEXT PRIMARY KEY,
--     label TEXT NOT NULL
-- );
-- CREATE TABLE IF NOT EXISTS source_options (
--     code TEXT PRIMARY KEY,
--     label TEXT NOT NULL
-- );
