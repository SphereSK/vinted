# Data Fields Guide

## Overview
This guide explains what data is captured by the scraper and how to get specific fields.

## Data Capture Levels

### 🚀 Level 1: Catalog API (Always Captured - FAST)
These fields are captured from every scrape **without** requiring `--fetch-details`:

| Field | Description | Example | Always Available |
|-------|-------------|---------|------------------|
| `vinted_id` | Vinted's internal item ID | `7298668670` | ✅ |
| `url` | Full URL to listing | `https://www.vinted.sk/items/...` | ✅ |
| `title` | Item title | `"PlayStation 5 Slim"` | ✅ |
| `price_cents` | Price in cents | `28400` (= €284.00) | ✅ |
| `currency` | Currency code | `"EUR"` | ✅ |
| `photo` | First photo URL | `https://images1.vinted.net/...` | ✅ |
| `seller_name` | Seller username | `"appleshop99"` | ✅ |
| `seller_id` | Seller ID | `"295840176"` | ✅ |
| `brand` | Brand name | `"PlayStation"` | ✅ |
| `condition` | Item condition | `"Veľmi dobré"` | ✅ |
| `category_id` | Category ID from search | `3026` | ✅ |
| `platform_ids` | Platform IDs from search | `[1281, 1280]` | ✅ |
| `first_seen_at` | When first scraped | `2025-10-12 10:05:46` | ✅ |
| `last_seen_at` | When last seen | `2025-10-12 20:09:46` | ✅ |

**Performance**: ~24 items/min

### 📝 Level 2: HTML Details (Requires `--fetch-details` - SLOW)
These fields require fetching and parsing the full HTML page:

| Field | Description | Example | Requires Flag |
|-------|-------------|---------|---------------|
| `description` | Full item description | `"je to dobra hra hral som..."` | `--fetch-details` |
| `language` | Page language code | `"sk"`, `"en"`, `"pl"` | `--fetch-details` |
| `photos` | All photo URLs (array) | `["url1", "url2", ...]` | `--fetch-details` |
| `shipping_cents` | Shipping cost in cents | `450` (= €4.50) | `--fetch-details` |

**Performance**: ~10 items/min (3x slower)

### ❌ Level 3: Not Available
These fields are **not captured** by the current scraper:

| Field | Why Not Available | Workaround |
|-------|-------------------|------------|
| `location` | Rendered client-side via JavaScript, requires browser automation | Click through to listing in web dashboard |
| `size` | Sometimes unavailable in catalog API | Use `--fetch-details` (experimental) |

## Usage Examples

### Example 1: Fast Scraping (Catalog Only)
```bash
# Get basic info for 1000 items quickly
vinted-scraper scrape \
  --search-text "ps5" \
  -c 3026 \
  -p 1281 \
  --no-proxy \
  --max-pages 42
```

**Captured**: Title, price, seller, condition, brand ✅
**Speed**: ~24 items/min
**Best for**: Price tracking, seller identification

### Example 2: With Descriptions (For English Game Filtering)
```bash
# Get descriptions to filter for English games
vinted-scraper scrape \
  --search-text "playstation" \
  -c 3026 \
  --fetch-details \
  --details-for-new-only \
  --no-proxy \
  --max-pages 10
```

**Captured**: All Level 1 + description + language ✅
**Speed**: ~10 items/min
**Best for**: Finding English descriptions, detailed analysis

### Example 3: Full Details for All Items
```bash
# Get everything for deep analysis
vinted-scraper scrape \
  --search-text "nintendo switch" \
  -c 3026 \
  --fetch-details \
  --no-proxy \
  --max-pages 5
```

**Captured**: All Level 1 + all Level 2 ✅
**Speed**: ~10 items/min
**Best for**: Complete item analysis

## Field Usage in Web Dashboard

### Filtering by Language
1. Run scraper with `--fetch-details`
2. Go to **Listings** → **Table View**
3. Look at **Lang** column
4. Filter for `"en"` to find English listings

### Viewing Descriptions
- In **Table View**, hover over description to see full text
- Or click **View** to open the listing on Vinted

### Price Change Tracking
- **↑ Red arrow** = Price increased
- **↓ Green arrow** = Price decreased
- Shows: `was €20.00` below current price
- Click **History** to see full price timeline

### Seller Information
- **Seller column** shows username (always available)
- Click username to filter by seller (future feature)

## Database Queries

### Find English Listings
```sql
SELECT title, description, language, price_cents/100.0 as price_eur
FROM vinted.listings
WHERE language = 'en'
  AND is_active = true
ORDER BY last_seen_at DESC;
```

### Find Price Drops
```sql
WITH latest_prices AS (
  SELECT listing_id, price_cents,
         LAG(price_cents) OVER (PARTITION BY listing_id ORDER BY observed_at) as prev_price
  FROM vinted.price_history
)
SELECT l.title, l.url,
       lp.prev_price/100.0 as was_eur,
       lp.price_cents/100.0 as now_eur,
       (lp.prev_price - lp.price_cents)/100.0 as saved_eur
FROM vinted.listings l
JOIN latest_prices lp ON l.id = lp.listing_id
WHERE lp.prev_price > lp.price_cents
  AND lp.prev_price IS NOT NULL
ORDER BY (lp.prev_price - lp.price_cents) DESC;
```

### Find Items from Specific Seller
```sql
SELECT title, price_cents/100.0 as price_eur, condition, last_seen_at
FROM vinted.listings
WHERE seller_name = 'appleshop99'
  AND is_active = true
ORDER BY last_seen_at DESC;
```

## Performance Optimization

### For Daily Scraping
Price history now tracks **daily** instead of hourly:
- First scrape: Creates initial price record
- Subsequent scrapes within 24h: No new price record (unless price changes)
- After 24h: Records price even if unchanged (for trend analysis)

**Recommended Schedule**:
```
0 */6 * * *  # Every 6 hours
```

This gives you 4 data points per day for trend analysis.

### For Fast Catalog Scraping
Skip `--fetch-details` to maximize speed:
```bash
vinted-scraper scrape \
  --search-text "ps5" \
  -c 3026 \
  --no-proxy \
  --max-pages 50 \
  --delay 0.5
```

**Speed**: Can scrape 1200 items in ~50 minutes

### For Detailed Analysis
Use `--details-for-new-only` to only fetch details for new items:
```bash
vinted-scraper scrape \
  --search-text "ps5" \
  -c 3026 \
  --fetch-details \
  --details-for-new-only \
  --no-proxy \
  --max-pages 20
```

**Speed**: Fast for re-scrapes (only new items get detailed fetch)

## Improvements Summary

### ✅ What Was Improved

1. **Price Tracking** - Changed from hourly to daily intervals
2. **Catalog Extraction** - Now extracts seller_name, seller_id, condition, brand from catalog API (no HTML fetch needed)
3. **Description & Language** - Added fields for filtering English games
4. **Category & Platform Tracking** - Saves which category/platform each listing belongs to
5. **Frontend Price Indicators** - Shows price changes with up/down arrows

### ⚠️ Known Limitations

1. **Location** - Not available in catalog API, requires browser automation to extract
2. **Size** - Sometimes missing in catalog, experimental in HTML parser
3. **Cloudflare Protection** - Requires session warmup, may fail occasionally

### 🔮 Future Improvements

1. **Browser Automation** - Use Playwright to get location data
2. **Seller Analytics** - Track seller reputation, response time
3. **Category Auto-Detection** - Infer category from title/description
4. **Multi-Language Search** - Translate search terms across locales

---

**Last Updated**: 2025-10-12
**Dashboard**: http://localhost:8000
