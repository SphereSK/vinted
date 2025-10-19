-- Migration: Add source column to listings table
-- Date: 2025-10-14
-- Description: Add source field to track which marketplace the listing came from (vinted, bazos, etc.)

-- For PostgreSQL
ALTER TABLE IF EXISTS vinted.listings
ADD COLUMN IF NOT EXISTS source VARCHAR(64) DEFAULT 'vinted';

-- For SQLite (if using SQLite, comment out PostgreSQL version above and use this)
-- ALTER TABLE listings ADD COLUMN source VARCHAR(64) DEFAULT 'vinted';

-- Update existing rows to have source='vinted'
UPDATE vinted.listings SET source = 'vinted' WHERE source IS NULL;

-- For SQLite version:
-- UPDATE listings SET source = 'vinted' WHERE source IS NULL;
