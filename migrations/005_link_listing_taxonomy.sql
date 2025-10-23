-- Migration: link listings to taxonomy master tables
-- ------------------------------------------------------------------
-- Adds integer primary keys to condition/source options, enforces unique codes,
-- and introduces foreign-key columns on listings for condition and source.

-- Condition options: ensure integer primary key and unique code
ALTER TABLE vinted.condition_options DROP CONSTRAINT IF EXISTS condition_options_pkey;
ALTER TABLE vinted.condition_options
    ADD COLUMN IF NOT EXISTS id SERIAL;
UPDATE vinted.condition_options SET id = nextval('vinted.condition_options_id_seq')
    WHERE id IS NULL;
ALTER TABLE vinted.condition_options
    ALTER COLUMN id SET NOT NULL,
    ADD CONSTRAINT condition_options_pkey PRIMARY KEY (id),
    ADD CONSTRAINT condition_options_code_key UNIQUE (code);

-- Source options: ensure integer primary key and unique code
ALTER TABLE vinted.source_options DROP CONSTRAINT IF EXISTS source_options_pkey;
ALTER TABLE vinted.source_options
    ADD COLUMN IF NOT EXISTS id SERIAL;
UPDATE vinted.source_options SET id = nextval('vinted.source_options_id_seq')
    WHERE id IS NULL;
ALTER TABLE vinted.source_options
    ALTER COLUMN id SET NOT NULL,
    ADD CONSTRAINT source_options_pkey PRIMARY KEY (id),
    ADD CONSTRAINT source_options_code_key UNIQUE (code);

-- Listings: add foreign keys for condition/source references
ALTER TABLE vinted.listings
    ADD COLUMN IF NOT EXISTS condition_option_id INTEGER,
    ADD COLUMN IF NOT EXISTS source_option_id INTEGER,
    ADD CONSTRAINT listings_condition_option_fk
        FOREIGN KEY (condition_option_id) REFERENCES vinted.condition_options(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    ADD CONSTRAINT listings_source_option_fk
        FOREIGN KEY (source_option_id) REFERENCES vinted.source_options(id)
        ON UPDATE CASCADE ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS ix_listings_condition_option_id
    ON vinted.listings(condition_option_id);
CREATE INDEX IF NOT EXISTS ix_listings_source_option_id
    ON vinted.listings(source_option_id);

-- SQLite variant (uncomment and adjust schema names when working with SQLite)
-- ALTER TABLE condition_options ADD COLUMN id INTEGER PRIMARY KEY AUTOINCREMENT;
-- ALTER TABLE condition_options ADD UNIQUE (code);
-- ALTER TABLE source_options ADD COLUMN id INTEGER PRIMARY KEY AUTOINCREMENT;
-- ALTER TABLE source_options ADD UNIQUE (code);
-- ALTER TABLE listings ADD COLUMN condition_option_id INTEGER REFERENCES condition_options(id);
-- ALTER TABLE listings ADD COLUMN source_option_id INTEGER REFERENCES source_options(id);
