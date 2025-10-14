# Video Game Platform Support

## Overview

Added comprehensive support for filtering video game listings by platform IDs. This allows you to search specifically for games compatible with PlayStation, Xbox, Nintendo, and other gaming platforms.

## Features Added

### 1. Platform IDs Database ✅

Added 18 gaming platforms to `app/utils/categories.py`:

**PlayStation**:
- 1281 - PlayStation 5
- 1280 - PlayStation 4
- 1279 - PlayStation 3
- 1278 - PlayStation 2
- 1277 - PlayStation 1
- 1286 - PlayStation Portable (PSP)
- 1287 - PlayStation Vita

**Xbox**:
- 1282 - Xbox Series X/S
- 1283 - Xbox One
- 1284 - Xbox 360
- 1285 - Xbox

**Nintendo**:
- 1288 - Nintendo Switch
- 1289 - Nintendo Wii U
- 1290 - Nintendo Wii
- 1291 - Nintendo DS
- 1292 - Nintendo 3DS
- 1293 - Nintendo GameCube
- 1294 - Nintendo 64
- 1295 - Game Boy

**Other**:
- 1296 - Sega
- 1297 - PC Gaming

### 2. CLI Commands ✅

**List All Platforms**:
```bash
vinted-scraper platforms
```

Output:
```
🎮 Video Game Platforms:

PlayStation:
    1281 - PlayStation 5
    1280 - PlayStation 4
    ...

💡 Use -p <ID> to filter by platform in scrape command
   Example: vinted-scraper scrape --search-text 'ps5' -c 3026 -p 1281 -p 1280
```

**Search Platforms**:
```bash
vinted-scraper platforms --search "play"
vinted-scraper platforms -s "xbox"
vinted-scraper platforms -s "switch"
```

### 3. Scraping with Platforms ✅

**Basic Usage**:
```bash
# PS5 games only
vinted-scraper scrape --search-text "ps5" -c 3026 -p 1281

# PS5 AND PS4 games
vinted-scraper scrape --search-text "playstation" -c 3026 -p 1281 -p 1280

# Xbox Series X/S games
vinted-scraper scrape --search-text "xbox" -c 3026 -p 1282

# Nintendo Switch games
vinted-scraper scrape --search-text "nintendo" -c 3026 -p 1288
```

**Your Example Command**:
```bash
vinted-scraper scrape \
  --search-text "ps5" \
  -c 3026 \
  -p 1281 \
  -p 1280 \
  --delay 1.5 \
  --no-proxy \
  --max-pages 5
```

This searches for:
- Text: "ps5"
- Category: 3026 (Video Games)
- Platforms: 1281 (PS5) + 1280 (PS4)
- Result: Gets games compatible with PlayStation 5 OR PlayStation 4

### 4. API Endpoint ✅

**Get Platforms List**:
```bash
curl http://localhost:8000/api/platforms
```

Response:
```json
[
  {
    "id": 1281,
    "name": "PlayStation 5"
  },
  {
    "id": 1280,
    "name": "PlayStation 4"
  },
  ...
]
```

### 5. Web UI Integration ✅

**Config Creation Form**:
- Added "Platform IDs" input field
- Shows common platform IDs with examples
- Comma-separated input (e.g., "1281, 1280")
- Helper text with quick reference
- Supports multiple platforms per config

**Form Fields**:
```
Name: PS5 & PS4 Games Monitor
Search Text: playstation
Categories: 3026
Platform IDs: 1281, 1280    ← NEW FIELD
Max Pages: 10
Cron Schedule: 0 */6 * * *
```

## How It Works

### URL Generation

When you use platform IDs, the scraper builds a URL like:
```
https://www.vinted.sk/catalog?
  search_text=ps5&
  catalog[0]=3026&
  video_game_platform_ids[0]=1281&
  video_game_platform_ids[1]=1280
```

This tells Vinted's API to only return items that:
1. Match "ps5" in title/description
2. Are in category 3026 (Video Games)
3. Are compatible with platform 1281 (PS5) OR 1280 (PS4)

### Database Storage

Platform IDs are stored in the `scrape_configs` table:
```sql
{
  "name": "PS5 Games Monitor",
  "search_text": "ps5",
  "categories": [3026],
  "platform_ids": [1281, 1280],  ← Stored as JSON array
  "max_pages": 10,
  ...
}
```

### Cron Job Generation

When synced to crontab, the scheduler generates:
```bash
cd /home/datament/project/vinted && vinted-scraper scrape \
  --search-text 'ps5' \
  --max-pages 10 \
  --delay 1.5 \
  -c 3026 \
  -p 1281 \
  -p 1280 \
  --no-proxy
```

## Use Cases

### Example 1: Monitor PS5 Games
```bash
vinted-scraper scrape \
  --search-text "ps5 games" \
  -c 3026 \
  -p 1281 \
  --max-pages 5
```
Result: Only PS5-specific games

### Example 2: Cross-Platform Games
```bash
vinted-scraper scrape \
  --search-text "call of duty" \
  -c 3026 \
  -p 1281 -p 1280 -p 1282 -p 1283 \
  --max-pages 10
```
Result: Games for PS5, PS4, Xbox Series X/S, Xbox One

### Example 3: Retro Gaming
```bash
vinted-scraper scrape \
  --search-text "retro games" \
  -c 3026 \
  -p 1277 -p 1278 -p 1294 -p 1295 \
  --max-pages 20
```
Result: PS1, PS2, N64, Game Boy games

### Example 4: Nintendo Switch
```bash
vinted-scraper scrape \
  --search-text "switch" \
  -c 3026 \
  -p 1288 \
  --max-pages 15
```
Result: Nintendo Switch games only

## Testing

### Test CLI
```bash
# List platforms
vinted-scraper platforms

# Search for PlayStation
vinted-scraper platforms -s "play"

# Search for Xbox
vinted-scraper platforms -s "xbox"

# Scrape with platform filter
vinted-scraper scrape --search-text "ps5" -c 3026 -p 1281 --max-pages 1
```

### Test API
```bash
# Get platforms
curl http://localhost:8000/api/platforms | python3 -m json.tool

# Create config with platforms
curl -X POST http://localhost:8000/api/configs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PS5 Games",
    "search_text": "ps5",
    "categories": [3026],
    "platform_ids": [1281, 1280],
    "max_pages": 5,
    "per_page": 24,
    "delay": 1.5
  }'
```

### Test Web UI
1. Open http://localhost:8000
2. Go to "Scrape Configs" tab
3. Click "+ New Configuration"
4. Fill in Platform IDs: `1281, 1280`
5. Create and run

## Files Modified

### `app/utils/categories.py`
- Added `VIDEO_GAME_PLATFORMS` dictionary (18 platforms)
- Added `list_video_game_platforms()` function
- Added `get_platform_name(platform_id)` function
- Added `search_platforms(query)` function

### `app/cli.py`
- Added `platforms` command
- Added platform search support
- Updated help text with examples

### `app/api/main.py`
- Added `GET /api/platforms` endpoint
- Returns list of all platforms

### `frontend/index.html`
- Added "Platform IDs" input field in config form
- Added helper text with common platform IDs
- Updated form handling to include platforms
- Added platform display in config list

## Benefits

1. **Precise Filtering**: Target specific gaming platforms
2. **Multi-Platform Support**: Combine multiple platforms (OR logic)
3. **Better Results**: Fewer irrelevant listings
4. **Organized Configs**: Separate configs per platform
5. **Price Comparison**: Compare same game across platforms

## Platform ID Reference Card

Quick reference for common use:

```
Most Common:
1281  PS5              Current gen Sony
1280  PS4              Previous gen Sony
1282  Xbox Series X/S  Current gen Microsoft
1283  Xbox One         Previous gen Microsoft
1288  Switch           Current gen Nintendo

Retro:
1279  PS3
1278  PS2
1277  PS1
1284  Xbox 360
1290  Wii
1294  N64

Handheld:
1286  PSP
1287  PS Vita
1291  Nintendo DS
1292  Nintendo 3DS
1295  Game Boy

Other:
1297  PC Gaming
1296  Sega (various)
```

## Summary

✅ 18 gaming platforms supported
✅ CLI command for listing/searching platforms
✅ API endpoint for platform data
✅ Web UI integration with form fields
✅ Automatic crontab generation with platforms
✅ Multiple platform filtering (OR logic)
✅ Compatible with existing scraper infrastructure

**Now you can filter video game listings by specific platforms!**

---

*Last Updated: 2025-10-12*
*Server: http://localhost:8000*
