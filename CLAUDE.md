# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Async Python scraper for Vinted marketplace with web dashboard for price tracking and automated scraping. Built with `vinted-api-kit` library, SQLAlchemy ORM, Typer CLI, FastAPI, and Vue.js. Features include price change tracking, seller identification, category/platform filtering, and scheduled scraping with cron integration.

## Architecture

### Core Components

1. **CLI Scraper** (`app/cli.py`) - Command-line interface for manual scraping
2. **Web Dashboard** (`frontend/index.html`) - Vue.js SPA for viewing listings and managing scrape configs
3. **FastAPI Backend** (`app/api/main.py`) - REST API serving listings, configs, and stats
4. **Database** (`app/db/models.py`) - PostgreSQL/SQLite with SQLAlchemy ORM
5. **Scheduler** (`app/scheduler.py`) - Cron integration for automated scraping

### Scraping Flow

1. **Session Warmup** - Captures Cloudflare cookies via direct HTTP connection (no proxy)
2. **Catalog API Scraping** - Fetches listings via `VintedApi` (fast, ~24 items/min)
3. **Optional HTML Details** - Fetches full HTML for descriptions/language (slow, ~10 items/min)
4. **Database Upsert** - Updates existing listings or inserts new ones
5. **Price History** - Records price changes daily for trend analysis

### Database Schema

#### `listings` Table
Main table with `url` as unique key. Captures:

**Always Available (Catalog API)**:
- `vinted_id` - Vinted's internal ID
- `url` - Full listing URL (unique key)
- `title`, `price_cents`, `currency` - Basic info
- `seller_name`, `seller_id` - Seller identification
- `brand`, `condition` - Item metadata
- `photo` - First photo URL
- `source` - Marketplace source (vinted, bazos, etc.)
- `category_id`, `platform_ids` - Filtering metadata
- `first_seen_at`, `last_seen_at` - Timestamps
- `is_active` - Deactivated if not seen recently

**With `--fetch-details` Flag**:
- `description` - Full item description
- `language` - Page language code (en, sk, pl, etc.)
- `photos` - JSON array of all photo URLs
- `shipping_cents` - Shipping cost

**Not Available**:
- `location` - Requires browser automation (JavaScript-rendered)

#### `price_history` Table
Child table tracking price changes:
- `listing_id` - Foreign key to listings
- `observed_at` - Timestamp of observation
- `price_cents` - Price at observation
- `currency` - Currency code

**Insertion Logic** (daily tracking):
1. First time seeing listing → INSERT
2. Price changed → INSERT
3. More than 24 hours since last observation → INSERT

#### `scrape_configs` Table
Automated scrape configurations:
- `name` - Config name
- `search_text` - Search query
- `categories`, `platform_ids` - Filters (JSON arrays)
- `max_pages`, `per_page`, `delay` - Scraping params
- `fetch_details` - Whether to fetch HTML details
- `cron_schedule` - Cron expression (e.g., `0 */6 * * *`)
- `is_active` - Whether config is enabled
- `last_run_at`, `last_run_status`, `last_run_items` - Execution tracking

## CLI Commands

### Scraper Commands

```bash
# View help
vinted-scraper --help
vinted-scraper scrape --help

# List categories and platforms
vinted-scraper categories
vinted-scraper categories --search "video"
vinted-scraper platforms
vinted-scraper platforms --search "playstation"

# Fast scraping (catalog only, 24 items/min)
vinted-scraper scrape \
  --search-text "ps5" \
  -c 3026 \
  -p 1281 \
  --no-proxy \
  --max-pages 10

# With descriptions for English filtering (10 items/min)
vinted-scraper scrape \
  --search-text "nintendo" \
  -c 3026 \
  --fetch-details \
  --details-for-new-only \
  --no-proxy \
  --max-pages 5

# Multiple platforms
vinted-scraper scrape \
  --search-text "playstation" \
  -c 3026 \
  -p 1281 -p 1280 -p 1279 \
  --no-proxy \
  --max-pages 20
```

### Language Detection (Post-Processing)

The `detect-language` command is a **post-processing step** that runs separately from the main scraper. This decouples slow HTML fetching from the fast catalog scraping flow.

**When to use**:
- After fast scraping without `--fetch-details`
- To fill in missing language data for existing listings
- To avoid slowing down the main scraping flow (keep it at 24 items/min)

**How it works**:
1. Finds listings with `language IS NULL`
2. Fetches HTML for each listing
3. Extracts language from HTML `<html lang="...">` tag
4. Updates database with detected language

```bash
# Process all listings without language
vinted-scraper detect-language

# Process only 10 listings (for testing)
vinted-scraper detect-language --limit 10

# Process only Vinted listings
vinted-scraper detect-language --source vinted

# Slower scraping to avoid rate limits
vinted-scraper detect-language --delay 2.0
```

**Workflow Example**:
```bash
# Step 1: Fast scraping (catalog only, ~24 items/min)
vinted-scraper scrape --search-text "ps5" -c 3026 -p 1281 --no-proxy --max-pages 20

# Step 2: Post-process language detection (~10 items/min, only for new items)
vinted-scraper detect-language --limit 50 --delay 1.5

# Step 3: Query for English listings
psql $DATABASE_URL -c "SELECT title, price_cents/100.0 FROM vinted.listings WHERE language='en' AND is_active=true;"
```

### Status Verification (Post-Processing)

The `verify-status` command is a **post-processing step** that solves a critical gap: items that disappear from catalog searches (sold/removed) are never checked again, leaving their status stale.

**When to use**:
- To verify status of items not seen in recent catalog scrapes
- To distinguish between sold items and removed items
- To maintain accurate `is_active`, `is_visible`, and `is_sold` flags
- Recommended: Run daily via cron

**How it works**:
1. Finds items marked `is_active=True` but not seen recently (configurable hours)
2. Fetches detail page for each item
3. Detects status:
   - **404 response** → Item removed (is_visible=False, is_sold=False)
   - **"Predané"/"Sprzedane"/"Prodáno"/"Sold" text** → Item sold (is_sold=True)
   - **Page loads normally** → Still available (is_visible=True)
4. Updates database with correct status

```bash
# Verify 100 oldest items not seen in last 24 hours
vinted-scraper verify-status

# Custom batch size and threshold
vinted-scraper verify-status --batch-size 50 --hours 48

# Faster checking (less delay between requests)
vinted-scraper verify-status --batch-size 200 --hours 24 --delay 1.5
```

**Performance**: ~3 seconds per item with default 2.0 delay (to avoid rate limits)

**Output Example**:
```
Verifying status of 5 items not seen in 24+ hours...
[1/5] Checking FC 26 na PS5...
  🔴 SOLD
[2/5] Checking Gran Turismo 7 gra ps5... (~0m 12s remaining)
  🔴 SOLD
[3/5] Checking FC25 PS5... (~0m 10s remaining)
  🔴 SOLD
[4/5] Checking Silent Hill 2... (~0m 6s remaining)
  🟡 REMOVED/UNAVAILABLE
[5/5] Checking Split Fiction... (~0m 3s remaining)
  🔴 SOLD

============================================================
Verification Complete!
Time: 0m 15s
Checked: 5 items
  🟢 Still available: 0
  🔴 Sold: 4
  🟡 Removed: 1
  ❌ Errors: 0
============================================================
```

**Recommended Workflow**:
```bash
# Step 1: Fast catalog scraping (finds new items, updates prices)
vinted-scraper scrape --search-text "ps5" -c 3026 -p 1281 --no-proxy --max-pages 20

# Step 2: Verify status of old items not in recent searches
vinted-scraper verify-status --batch-size 100 --hours 24

# Step 3: Query accurate active listings
psql $DATABASE_URL -c "SELECT title, price_cents/100.0 FROM vinted.listings WHERE is_active=true AND is_visible=true ORDER BY last_seen_at DESC;"
```

### Web Dashboard

```bash
# Start web server
python3 -m app.api.main

# Access dashboard
http://localhost:8000
```

**Features**:
- View listings in grid or table view
- See price changes with up/down arrows
- Create scrape configurations
- Schedule automated scraping with cron
- View price history charts
- Filter by category/platform/seller

## Development

### Setup

```bash
# Install dependencies
pip install -e .

# Configure database (PostgreSQL recommended)
export DATABASE_URL="postgresql+asyncpg://vinted_user:password@localhost:6432/vinted_db"

# Or use SQLite (default)
export DATABASE_URL="sqlite+aiosqlite:///./vinted.db"

# Start API server
python3 -m app.api.main
```

### Adding a New Field to Database

1. **Add column to model** (`app/db/models.py`):
```python
class Listing(Base):
    # ...existing fields...
    new_field: Mapped[Optional[str]] = mapped_column(String(256))
```

2. **Update upsert logic** (`app/ingest.py`):
```python
stmt = stmt.on_conflict_do_update(
    index_elements=["url"],
    set_={
        # ...existing fields...
        "new_field": stmt.excluded.new_field,
    }
)
```

3. **Parse field from catalog or HTML** (`app/scraper/parse_header.py` or `parse_detail.py`):
```python
# In parse_catalog_item() or parse_detail_html()
return {
    # ...existing fields...
    "new_field": extracted_value,
}
```

4. **Run database migration**:
```bash
psql $DATABASE_URL -c "ALTER TABLE vinted.listings ADD COLUMN IF NOT EXISTS new_field VARCHAR(256);"
```

5. **Update API schemas** (`app/api/schemas.py`):
```python
class ListingResponse(ListingBase):
    # ...existing fields...
    new_field: Optional[str] = None
```

### Adding a New CLI Option

1. **Update command** (`app/cli.py`):
```python
@app.command()
def scrape(
    # ...existing params...
    new_option: bool = typer.Option(False, "--new-option", help="Description"),
):
    asyncio.run(scrape_and_store(
        # ...existing params...
        new_option=new_option,
    ))
```

2. **Update scraper** (`app/ingest.py`):
```python
async def scrape_and_store(
    # ...existing params...
    new_option: bool = False,
):
    # Use new_option in scraping logic
```

## Key Implementation Details

### Data Extraction Strategy

**Level 1 - Catalog API (Always Captured)**:
- Fast extraction from `VintedApi.search_items()`
- Parses `raw_data` dict for seller/brand/condition
- ~24 items/min throughput
- File: `app/scraper/parse_header.py`

**Level 2 - HTML Details (Optional)**:
- Slow extraction via `requests.get()` + BeautifulSoup
- Parses `window.__PRELOADED_STATE__` JSON for shipping/location
- CSS selectors for description/language
- ~10 items/min throughput (3x slower)
- File: `app/scraper/parse_detail.py`

### Anti-Bot Strategy

1. **Direct Connection** - No proxy (controlled by `--no-proxy` flag)
2. **Session Warmup** - Pre-fetches homepage to capture Cloudflare cookies (respects `--no-proxy`)
3. **Cookie Persistence** - Saves/reloads cookies from `cookies.txt`
4. **Random Delays** - `delay + random.uniform(0, 0.5)` between requests
5. **Automatic 403 Retry** - Waits configurable time (controlled by `--error-wait`, `--max-retries`) and retries on rate limits
6. **Browser Fallback** - Falls back to Playwright if warmup fails (experimental)

**Note**: Proxy rotation has been deprecated in favor of direct connections with proper cookies, or controlled proxy usage via CLI.

### 403 Error Handling

When Vinted returns 403 (Forbidden) errors, the scraper automatically:
- Detects the error
- Waits a configurable period (default: 30 minutes)
- Shows countdown timer with progress updates
- Retries the failed page
- Continues with next page after max retries (default: 3)

**CLI Parameters**:
```bash
  --base-url TEXT             Base Vinted catalog URL (e.g., https://www.vinted.com/catalog)
  --locale TEXT               Locale code [default: sk]

SCRAPING:
  --max-pages INTEGER         Pages to scrape [default: 5]
  --per-page INTEGER          Items per page [default: 24]
  --delay FLOAT               Delay between requests [default: 1.0]
  --no-proxy                  Skip proxy (recommended!)

ERROR HANDLING:
  --error-wait INTEGER        Minutes to wait on 403 errors [default: 30] (now controls retry_with_backoff initial_delay)
  --max-retries INTEGER       Max retry attempts [default: 3] (now controls retry_with_backoff retries)
```

**Example**:
```bash
# Large scrape with custom error handling
vinted-scraper scrape --search-text "ps5" -c 3026 -p 1281 \
  --no-proxy --max-pages 50 \
  --error-wait 15 --max-retries 5
```

**Output on 403**:
```
=== Page 7/50 === [144 items, 9m 24s elapsed, ~67m 54s remaining]
  ⚠️  403 Error detected (attempt 1/3)
  ⏳ Waiting 30 minutes before retry...
     Will resume at: 2025-10-14 15:45:00
     29 minute(s) remaining...
```

### Upsert Logic

PostgreSQL `INSERT ... ON CONFLICT DO UPDATE` ensures:
- Existing listings update all fields + `last_seen_at`
- New listings insert with `first_seen_at = last_seen_at = now()`
- `is_active` resets to `True` on re-observation
- Price changes trigger `PriceHistory` insert

**Why Upsert?** Vinted returns duplicate items across pages, so 5 pages × 24 items = 120 items might only yield ~60 unique listings.

### Price Tracking

Daily price tracking (24-hour interval):
- Inserts price history on first observation
- Inserts on price change
- Inserts once per day even if price unchanged (for trend analysis)

This allows scheduled scraping once daily while still building historical price data.

### Frontend Price Indicators

Vue.js frontend shows:
- Current price in large text
- Previous price with arrow indicator:
  - 🔴 ↑ = Price increased
  - 🟢 ↓ = Price decreased
  - ⚪ → = Price unchanged
- Click "History" to see full price timeline

## Module Structure

```
vinted/
├── app/
│   ├── cli.py              # Typer CLI commands
│   ├── config.py           # Environment variable settings
│   ├── ingest.py           # Main scraping logic + upsert
│   ├── postprocess.py      # Post-processing (language detection, etc.)
│   ├── verify_status.py    # Post-processing (item status verification)
│   ├── scheduler.py        # Cron integration
│   ├── api/
│   │   ├── main.py         # FastAPI app
│   │   └── schemas.py      # Pydantic request/response models
│   ├── db/
│   │   ├── models.py       # SQLAlchemy ORM (Listing, PriceHistory, ScrapeConfig)
│   │   └── session.py      # Async engine + sessionmaker
│   ├── scraper/
│   │   ├── parse_header.py     # Catalog API extraction
│   │   ├── parse_detail.py     # HTML detail extraction
│   │   ├── session_warmup.py   # Cookie capture
│   │   └── vinted_client.py    # Helper wrappers
│   ├── proxies/
│   │   └── fetch_and_test.py   # Proxy fetching (deprecated)
│   └── utils/
│       ├── url.py          # URL builders
│       └── categories.py   # Category/platform lists
├── migrations/
│   ├── 001_add_source_column.sql  # Database migrations
│   └── README.md           # Migration instructions
├── frontend/
│   └── index.html          # Vue.js SPA dashboard
├── CLAUDE.md               # This file
├── DATA_FIELDS_GUIDE.md    # Field availability reference
├── SCRAPER_BEHAVIOR.md     # Explanation of duplicate handling
├── setup.py                # Package definition
└── .env                    # Configuration (DATABASE_URL, etc.)
```

## Common Use Cases

### Finding English Games

```bash
# Scrape with descriptions
vinted-scraper scrape \
  --search-text "ps5" \
  -c 3026 -p 1281 \
  --fetch-details \
  --no-proxy \
  --max-pages 10

# Query database for English listings
psql $DATABASE_URL -c "
SELECT title, description, price_cents/100.0 as price_eur
FROM vinted.listings
WHERE language = 'en' AND is_active = true
ORDER BY price_cents ASC;
"
```

### Tracking Price Drops

```bash
# Set up automated daily scraping in web dashboard
# Schedule: 0 8 * * * (every day at 8am)

# Query for price drops
psql $DATABASE_URL -c "
WITH latest_prices AS (
  SELECT listing_id, price_cents,
         LAG(price_cents) OVER (PARTITION BY listing_id ORDER BY observed_at) as prev_price
  FROM vinted.price_history
)
SELECT l.title, l.url,
       lp.prev_price/100.0 as was_eur,
       lp.price_cents/100.0 as now_eur
FROM vinted.listings l
JOIN latest_prices lp ON l.id = lp.listing_id
WHERE lp.prev_price > lp.price_cents
ORDER BY (lp.prev_price - lp.price_cents) DESC;
"
```

### Comparing Sellers

```bash
# Find sellers with best average prices
psql $DATABASE_URL -c "
SELECT seller_name, COUNT(*) as listings, AVG(price_cents)/100.0 as avg_price
FROM vinted.listings
WHERE category_id = 3026 AND is_active = true
GROUP BY seller_name
HAVING COUNT(*) >= 3
ORDER BY avg_price ASC
LIMIT 20;
"
```

## Dependencies

- `vinted_scraper==3.0.0a1` - Vinted API client (unstable alpha)
- `SQLAlchemy[asyncio]` - Async ORM
- `asyncpg` - PostgreSQL async driver
- `aiosqlite` - SQLite async driver
- `fastapi` - Web API framework
- `uvicorn` - ASGI server
- `typer` - CLI framework
- `python-dotenv` - Environment variables
- `requests` - HTTP client for HTML details
- `beautifulsoup4` - HTML parsing
- `python-crontab` - Cron integration

## Configuration

All settings via `.env` file:

```bash
# Database (PostgreSQL recommended for production)
DATABASE_URL=postgresql+asyncpg://vinted_user:password@127.0.0.1:6432/vinted_db

# Or SQLite (default for development)
# DATABASE_URL=sqlite+aiosqlite:///./vinted.db

# Scraping defaults
VINTED_BASE_URL=https://www.vinted.sk/catalog
VINTED_FILTERS=catalog[]=3026&video_game_platform_ids[]=1281
MAX_PAGES=15
PER_PAGE=24
REQUEST_DELAY=1.5

# Logging
LOG_LEVEL=INFO
ENABLE_DB_LOGGING=true
```

## Performance

| Operation | Throughput | Use Case |
|-----------|------------|----------|
| Catalog scraping | ~24 items/min | Price tracking, seller ID |
| With HTML details | ~10 items/min | Descriptions, language filtering |
| Database upsert | ~1000 ops/sec | Batch imports |
| API queries | ~100 req/sec | Web dashboard |

## Limitations

1. **Location field** - Not available in catalog API, requires browser automation
2. **Duplicate items** - Vinted returns overlapping results across pages
3. **Rate limiting** - Increase `--delay` if you hit limits
4. **Cloudflare** - Requires session warmup, may fail occasionally
5. **Alpha API** - `vinted-api-kit` is unstable, field names change

## Future Improvements

1. Browser automation for location extraction
2. Seller reputation tracking
3. Multi-supplier comparison (Vinted + others)
4. Price prediction ML model
5. Real-time notifications on price drops
6. Multi-language search translation

---

**Dashboard**: http://localhost:8000
**Last Updated**: 2025-10-28
**Documentation**: See `DATA_FIELDS_GUIDE.md` and `SCRAPER_BEHAVIOR.md`

## Recent Changes

### 2025-10-28: Item Status Verification & Tracking
- Added `is_visible` field to track item visibility from catalog API (fast detection)
- Fixed pagination bug where scraper looped through same pages repeatedly
- Created `verify-status` command for proactive status checking of tracked items
- Multi-language sold detection (Slovak, Polish, Czech, English)
- Distinguishes between sold items vs removed items (404)
- Added database migration: `migrations/007_add_is_visible_column.sql`
- Updated catalog parser to extract `is_visible` from raw_data
- Updated upsert logic to sync `is_active` with `is_visible`
- **Recommended**: Run `verify-status` daily via cron to maintain accurate item status

### 2025-10-14: Post-Processing & Multi-Source Support
- Added `source` field to listings table for multi-marketplace support (vinted, bazos, etc.)
- Created `detect-language` post-processing command to decouple language detection from main scraping
- Added database migration: `migrations/001_add_source_column.sql`
- Updated API schemas to include source field
- All existing listings default to `source='vinted'`
- **NEW**: Automatic 403 error retry with configurable wait times (`--error-wait`, `--max-retries`)
- System automatically waits and retries on rate limits, shows countdown timer

## Task Master AI Instructions
**Import Task Master's development workflow commands and guidelines, treat as if import is in the main CLAUDE.md file.**
@./.taskmaster/CLAUDE.md
