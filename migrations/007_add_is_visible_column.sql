-- Migration: Add is_visible column for tracking item availability
-- Date: 2025-10-28
-- Description: Adds is_visible boolean field to track if items are visible on Vinted
--              This allows fast detection of sold/removed items without fetching HTML

-- PostgreSQL migration
DO $$
BEGIN
    -- Add is_visible column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'vinted'
        AND table_name = 'listings'
        AND column_name = 'is_visible'
    ) THEN
        ALTER TABLE vinted.listings
        ADD COLUMN is_visible BOOLEAN DEFAULT TRUE NOT NULL;

        RAISE NOTICE 'Added is_visible column to vinted.listings';
    ELSE
        RAISE NOTICE 'Column is_visible already exists, skipping';
    END IF;

    -- Create index on is_visible for fast queries
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE schemaname = 'vinted'
        AND tablename = 'listings'
        AND indexname = 'ix_listings_is_visible'
    ) THEN
        CREATE INDEX ix_listings_is_visible ON vinted.listings(is_visible);

        RAISE NOTICE 'Created index ix_listings_is_visible';
    ELSE
        RAISE NOTICE 'Index ix_listings_is_visible already exists, skipping';
    END IF;

    -- Update existing inactive items to be invisible
    UPDATE vinted.listings
    SET is_visible = FALSE
    WHERE is_active = FALSE;

    RAISE NOTICE 'Updated existing inactive items to is_visible=FALSE';

END $$;

-- SQLite migration (for development)
-- SQLite doesn't support DO blocks, so run these manually:
-- ALTER TABLE listings ADD COLUMN is_visible BOOLEAN DEFAULT 1 NOT NULL;
-- CREATE INDEX IF NOT EXISTS ix_listings_is_visible ON listings(is_visible);
-- UPDATE listings SET is_visible = 0 WHERE is_active = 0;

-- Rollback (if needed):
-- DROP INDEX IF EXISTS vinted.ix_listings_is_visible;
-- ALTER TABLE vinted.listings DROP COLUMN IF EXISTS is_visible;
