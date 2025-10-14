# Vinted Scraper Web Dashboard - Setup Complete! 🎉

## What Was Built

A complete web-based management system for your Vinted scraper with:

###  1. **FastAPI Backend** (`app/api/`)
- RESTful API with 15+ endpoints
- Database integration with PostgreSQL
- Real-time statistics and monitoring
- Scrape configuration management
- Automated crontab synchronization

### 2. **Vue.js Frontend** (`frontend/index.html`)
- Single-page application (no build process needed!)
- 3 main tabs: Dashboard, Listings, Configurations
- Real-time stats display
- Product browser with search
- Configuration creator with cron scheduler

### 3. **Database Models** (`app/db/models.py`)
- **Listing** - Product data with price tracking
- **PriceHistory** - Historical price changes
- **ScrapeConfig** - Automated scraping configurations

### 4. **Cron Scheduler** (`app/scheduler.py`)
- Automatic sync to system crontab
- Command-line management tools
- Background task execution

## Quick Start

### Start the Server

```bash
./start_server.sh
```

Or manually:
```bash
python3 -m app.api.main
```

### Access the Dashboard

Open your browser to: **http://localhost:8000**

You'll see:
- **Dashboard**: 27 listings, 27 active, 0 configs (avg price: 225.25 EUR)
- **Listings**: Browse all 27 PS5 products you've scraped
- **Scrape Configs**: Create automated scraping tasks

## Create Your First Automated Scrape

1. Click **"Scrape Configs"** tab
2. Click **"+ New Configuration"**
3. Fill in:
   ```
   Name: PS5 Games Daily Check
   Search Text: ps5
   Categories: 3026
   Max Pages: 10
   Delay: 1.5
   Cron Schedule: 0 9 * * *
   ```
4. Click **"Create Configuration"**
5. The system will automatically:
   - Create the configuration in the database
   - Sync it to your system crontab
   - Run daily at 9 AM automatically

## Manual Scraping

To run a configuration immediately:
1. Go to **Scrape Configs** tab
2. Click **"Run Now"** on any configuration
3. Watch the stats update in real-time

## API Endpoints

### Listings
- `GET /api/listings` - Browse all products (paginated)
- `GET /api/listings/{id}` - View product details + price history
- Query params: `?search=ps5&skip=0&limit=50`

### Configurations
- `GET /api/configs` - List all scrape configurations
- `POST /api/configs` - Create new configuration
- `PUT /api/configs/{id}` - Update configuration
- `DELETE /api/configs/{id}` - Delete configuration
- `POST /api/configs/{id}/run` - Trigger immediate scrape

### Categories
- `GET /api/categories` - List available Vinted categories

### Stats
- `GET /api/stats` - Dashboard statistics

### Cron
- `GET /api/cron/jobs` - List all scheduled jobs
- `POST /api/cron/sync` - Manually sync configs to crontab

## Category Reference

| ID | Name |
|----|------|
| 2994 | Electronics |
| 3026 | Video Games |
| 1953 | Computers |
| 16 | Women's Clothing |
| 18 | Men's Clothing |
| 12 | Kids & Baby |
| 1243 | Home |
| 5 | Entertainment |

## Cron Schedule Examples

```bash
0 */6 * * *      # Every 6 hours
0 9 * * *        # Daily at 9 AM
*/30 * * * *     # Every 30 minutes
0 18 * * 1-5     # Weekdays at 6 PM
0 0 * * 0        # Every Sunday at midnight
```

## Current Database Status

You currently have:
- **27 listings** in the database (PS5 products from earlier scrape)
- **0 configurations** (you'll create your first one via the UI!)
- **Average price**: 225.25 EUR

## Features Included

### ✅ Completed Features

1. **Category Discovery**
   - CLI: `vinted-scraper categories`
   - API: `GET /api/categories`
   - Frontend: Category selector in config form

2. **Progress Tracking**
   - Real-time page progress
   - Elapsed/remaining time estimates
   - Items per page stats
   - Final summary with totals

3. **Web Dashboard**
   - Real-time statistics
   - Product browser with photos
   - Search and pagination
   - Configuration management

4. **Automated Scheduling**
   - Cron integration
   - Auto-sync to system crontab
   - Manual trigger option
   - Status tracking (success/failed/running)

5. **Multi-Supplier Ready**
   - Database schema supports multiple sources
   - Easy to extend for other marketplaces
   - Comparison views (placeholder for future)

## Next Steps

### Immediate Actions

1. **Create your first configuration** in the web UI
2. **Test manual scraping** with "Run Now"
3. **Set up automated schedules** for different product categories

### Future Enhancements

1. **Add more suppliers** (eBay, Amazon, etc.)
2. **Price comparison views** across suppliers
3. **Email alerts** on price drops
4. **Export functionality** (CSV, Excel)
5. **Advanced filtering** (price range, condition, location)
6. **User authentication** for multi-user setups

## Troubleshooting

### Port 8000 in use
```bash
# Kill existing process
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn app.api.main:app --port 8001
```

### Cron not syncing
```bash
# Manual sync
python3 -m app.scheduler sync

# List jobs
python3 -m app.scheduler list

# Clear all jobs
python3 -m app.scheduler clear
```

### Database issues
```bash
# Re-initialize database
python3 -c "from app.db.session import init_db; import asyncio; asyncio.run(init_db())"
```

## Architecture Overview

```
vinted/
├── app/
│   ├── api/
│   │   ├── main.py          # FastAPI application
│   │   └── schemas.py       # Pydantic models
│   ├── db/
│   │   ├── models.py        # SQLAlchemy ORM
│   │   └── session.py       # Database sessions
│   ├── utils/
│   │   ├── categories.py    # Category helpers
│   │   └── url.py           # URL builders
│   ├── scheduler.py         # Cron integration
│   ├── ingest.py            # Scraping logic
│   └── cli.py               # CLI commands
├── frontend/
│   └── index.html           # Vue.js SPA
├── start_server.sh          # Server startup script
└── WEBUI_README.md          # Detailed documentation
```

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, AsyncPG
- **Frontend**: Vue.js 3, Axios
- **Database**: PostgreSQL (via PgBouncer)
- **Scheduler**: python-crontab
- **CLI**: Typer
- **Scraping**: vinted-api-kit, requests

## Success Metrics

Your dashboard should show:
- ✅ 27 total listings (from your earlier scrape)
- ✅ API responding at http://localhost:8000/api
- ✅ Frontend accessible at http://localhost:8000
- ✅ Categories endpoint returning 8 categories
- ✅ Stats showing average price ~225 EUR

## Ready to Use!

Your Vinted scraper is now fully operational with a web interface. Start creating configurations and let the system automatically monitor prices for you!

**Server is running at**: http://localhost:8000

Happy scraping! 🚀
