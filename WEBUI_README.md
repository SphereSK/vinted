# Vinted Scraper Web UI

Complete web interface for managing Vinted product scraping, price tracking, and automated scheduling.

## Features

### Dashboard
- Real-time statistics (total listings, active configs, daily scrapes)
- Average price tracking across all products
- Quick overview of scraping activity

### Listings Browser
- View all scraped products with photos
- Search and filter functionality
- Price history tracking
- Direct links to Vinted listings
- Seller information and location

### Scrape Configurations
- Create automated scraping tasks
- Configure search parameters (categories, keywords, platforms)
- Set cron schedules for recurring scrapes
- Monitor scrape status and results
- Run scrapes manually on-demand

### Automated Scheduling (Cron Integration)
- Set cron schedules directly from web UI
- Automatic sync to system crontab
- View scheduled jobs
- Examples:
  - `0 */6 * * *` - Every 6 hours
  - `0 9 * * *` - Daily at 9 AM
  - `*/30 * * * *` - Every 30 minutes

## Quick Start

### 1. Start the Server

```bash
./start_server.sh
```

Or manually:
```bash
python3 -m app.api.main
```

### 2. Open Browser

Navigate to: **http://localhost:8000**

### 3. Create Your First Configuration

1. Go to "Scrape Configs" tab
2. Click "+ New Configuration"
3. Fill in the form:
   - **Name**: "PS5 Games Monitor"
   - **Search Text**: "ps5"
   - **Categories**: 3026 (Video Games)
   - **Max Pages**: 5
   - **Delay**: 1.0s
   - **Cron Schedule**: `0 */6 * * *` (every 6 hours)
4. Click "Create Configuration"

### 4. Run Manually or Wait for Cron

- Click "Run Now" to test immediately
- Or wait for the cron job to execute automatically

## API Endpoints

### Listings
- `GET /api/listings` - List all listings (paginated)
- `GET /api/listings/{id}` - Get listing details with price history

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

### Cron Management
- `GET /api/cron/jobs` - List scheduled cron jobs
- `POST /api/cron/sync` - Manually sync configs to crontab

## Category IDs Reference

### Electronics & Gaming
- `2994` - Electronics
- `3026` - Video Games
- `1953` - Computers

### Fashion
- `16` - Women's Clothing
- `18` - Men's Clothing
- `12` - Kids & Baby

### Home & Lifestyle
- `1243` - Home
- `5` - Entertainment

## Cron Schedule Examples

```bash
# Every hour
0 * * * *

# Every 6 hours
0 */6 * * *

# Daily at 9 AM
0 9 * * *

# Every weekday at 6 PM
0 18 * * 1-5

# Every 30 minutes
*/30 * * * *
```

## Database Schema

### Listings
- Product details (title, price, brand, condition)
- Seller information
- Photos
- First/last seen timestamps
- Active status tracking

### Price History
- Historical price tracking
- Automatic insertion on price changes
- Timestamp for each observation

### Scrape Configs
- Configuration parameters
- Cron schedule
- Last run status and statistics
- Active/inactive toggle

## Future: Multi-Supplier Comparison

The system is designed to support multiple suppliers:
- Add new supplier models (similar to `Listing`)
- Create comparison views in frontend
- Price alerts when better deals found elsewhere
- Unified search across all suppliers

## Troubleshooting

### Port 8000 already in use
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn app.api.main:app --port 8001
```

### Cron jobs not running
```bash
# Check system crontab
crontab -l | grep vinted

# Manually sync
python3 -m app.scheduler sync

# View logs
tail -f /var/log/syslog | grep vinted
```

### Database not updating
```bash
# Check database connection
python3 -c "from app.db.session import Session; import asyncio; asyncio.run(Session().__aenter__())"

# Re-initialize database
python3 -c "from app.db.session import init_db; import asyncio; asyncio.run(init_db())"
```

## Architecture

```
frontend/
  index.html          # Vue.js single-page app

app/
  api/
    main.py           # FastAPI application
    schemas.py        # Pydantic models
  db/
    models.py         # SQLAlchemy models (Listing, PriceHistory, ScrapeConfig)
    session.py        # Database session management
  utils/
    categories.py     # Category helpers
  scheduler.py        # Cron integration
  ingest.py           # Main scraping logic
```

## Production Deployment

For production use:

1. **Use PostgreSQL** (not SQLite)
   ```bash
   export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/vinted"
   ```

2. **Run with Gunicorn**
   ```bash
   gunicorn app.api.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

3. **Use proper CORS settings**
   Update `allow_origins` in `app/api/main.py`

4. **Set up reverse proxy** (Nginx/Caddy)
   ```nginx
   location / {
       proxy_pass http://localhost:8000;
   }
   ```

5. **Background task queue** (Celery/RQ)
   Replace `asyncio.create_task()` with proper queue

## License

MIT
