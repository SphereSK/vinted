# Vinted Scraper Behavior Explained

## What's Happening When You Scrape

### Duplicate Items Across Pages
When you run:
```bash
vinted-scraper scrape --search-text "ps5" -c 3026 -p 1281 --max-pages 5
```

You expect: 5 pages × 24 items = **120 items**

You get in DB: **~60 unique items**

**Why?** Vinted's API returns **overlapping results** across pages. Many items appear on multiple pages. For example:
- "PlayStation 5 | 284.73 EUR" appears on page 1 AND page 2
- This is Vinted's behavior, not a bug in our scraper

### Database Upsert (INSERT or UPDATE)
Our scraper uses **UPSERT** logic:
- **First time seeing item**: INSERT new record
- **Seeing same item again**: UPDATE existing record with:
  - Latest price
  - Updated `last_seen_at` timestamp ✅
  - All other fields refreshed

**Example:**
```
Scrape Run 1 (10:00 AM): Item "PS5 Console" at €300 → INSERT
Scrape Run 2 (02:00 PM): Item "PS5 Console" at €300 → UPDATE last_seen_at
Scrape Run 3 (06:00 PM): Item "PS5 Console" at €290 → UPDATE price + INSERT price_history
```

## Database Tables

### listings
- Contains **unique items** (one row per URL)
- `first_seen_at`: When we first discovered the item
- `last_seen_at`: When we last saw the item (updated on every scrape) ✅
- `price_cents`: Current price

### price_history
- Contains **price observations** over time
- New record inserted when:
  1. First time seeing the item
  2. Price changes from last recorded price
  3. **NEW**: More than 24 hours has passed since last observation (daily tracking)

This allows you to:
- Track price trends over time
- See price changes with timestamps
- Build historical price charts

## Recent Improvements

### 1. Enhanced Price Tracking (Daily) ✅
**Before**: Only tracked price changes
**After**: Tracks prices daily + on changes

This means if you run scheduled scrapes once or twice daily, you'll build up a price history showing:
- When prices went up ↑
- When prices went down ↓
- When prices stayed stable →
- Historical trends for each listing

### 2. Added Description & Language Fields ✅
New columns in `listings` table:
- `description`: Full item description
- `language`: Language code (e.g., "en", "sk", "fr")
- `category_id`: Which category (3026 = Video Games)
- `platform_ids`: Which platforms ([1281] = PS5)

Use `--fetch-details` to populate these fields:
```bash
vinted-scraper scrape \
  --search-text "ps5" \
  -c 3026 \
  -p 1281 \
  --fetch-details \
  --details-for-new-only \
  --no-proxy \
  --max-pages 5
```

### 3. Frontend Price Change Indicators ✅
The web dashboard now shows:
- Current price in large text
- Previous price below
- Color-coded arrows:
  - 🔴 ↑ = Price went up
  - 🟢 ↓ = Price went down
  - ⚪ → = Price unchanged

## Checking Your Data

### Total Listings
```bash
psql $DATABASE_URL -c "SELECT COUNT(*) FROM vinted.listings;"
```

### Price History Count
```bash
psql $DATABASE_URL -c "SELECT COUNT(*) FROM vinted.price_history;"
```

### Items with Multiple Price Observations
```bash
psql $DATABASE_URL -c "
SELECT l.title, COUNT(ph.id) as observations
FROM vinted.listings l
JOIN vinted.price_history ph ON l.id = ph.listing_id
GROUP BY l.id, l.title
HAVING COUNT(ph.id) > 1
ORDER BY observations DESC;
"
```

### Recently Updated Items
```bash
psql $DATABASE_URL -c "
SELECT title, price_cents/100.0 as price_eur,
       first_seen_at, last_seen_at,
       last_seen_at - first_seen_at as time_tracked
FROM vinted.listings
ORDER BY last_seen_at DESC
LIMIT 10;
"
```

## Recommended Usage

### For Price Tracking
Set up a scheduled scrape once or twice daily:
```bash
# In web dashboard: Create config with cron schedule

# Option 1: Once daily at 8am
cron_schedule: "0 8 * * *"

# Option 2: Twice daily at 8am and 8pm
cron_schedule: "0 8,20 * * *"
```

After a few days/weeks, you'll have rich price history showing trends.

### For Finding English Games
1. Enable `fetch_details` in your scrape config
2. Filter by `language = 'en'` in the web dashboard table view
3. Read descriptions to verify game details

### For Monitoring Specific Platforms
Use platform filters:
```bash
vinted-scraper scrape \
  --search-text "playstation" \
  -c 3026 \
  -p 1281 \    # PS5
  -p 1280 \    # PS4
  --max-pages 10
```

## Summary

✅ **Upserts working correctly** - Updates existing items instead of creating duplicates
✅ **Timestamps updating** - `last_seen_at` refreshed on every scrape
✅ **Price history improved** - Now tracks daily observations + changes
✅ **Seller data captured** - seller_name, seller_id, brand, condition from catalog API
✅ **New fields added** - Description, language, category, platforms (with --fetch-details)
✅ **Frontend enhanced** - Price change indicators with up/down arrows, table view with descriptions

The behavior you're seeing is **correct**. Vinted returns overlapping results, and our scraper handles this properly by updating existing records. Over time, as you run scheduled scrapes, you'll build up a rich price history dataset.

### What Data is Always Captured (Fast, ~24 items/min)
- Title, price, currency
- Seller name and ID
- Brand, condition
- Category and platform IDs
- First/last seen timestamps

### What Data Requires --fetch-details (Slow, ~10 items/min)
- Full description
- Language code
- All photo URLs
- Shipping costs

### What Data is Not Available
- Location (requires browser automation with JavaScript rendering)

---

**Dashboard**: http://localhost:8000
**Documentation**: See `CLAUDE.md` and `DATA_FIELDS_GUIDE.md`
**Last Updated**: 2025-10-12
