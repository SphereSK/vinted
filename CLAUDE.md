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

1. **Direct Connection** - No proxy (recommended with `--no-proxy`)
2. **Session Warmup** - Pre-fetches homepage to capture Cloudflare cookies
3. **Cookie Persistence** - Saves/reloads cookies from `cookies.txt`
4. **Random Delays** - `delay + random.uniform(0, 0.5)` between requests
5. **Browser Fallback** - Falls back to Playwright if warmup fails (experimental)

**Note**: Proxy rotation has been deprecated in favor of direct connections with proper cookies.

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
**Last Updated**: 2025-10-12
**Documentation**: See `DATA_FIELDS_GUIDE.md` and `SCRAPER_BEHAVIOR.md`
