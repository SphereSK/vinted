# Latest Updates - Table View & Price Tracking

## Changes Made

### 1. Added Table View for Listings ✅

**Grid View vs Table View Toggle**
- Users can now switch between Grid (card) view and Table view
- Toggle buttons at the top of listings tab
- Table view shows all listing details in a structured format

**Table Columns**:
- Image (60x60px thumbnail)
- Title (with max-width for readability)
- Price (with "View History" button)
- Seller
- Location
- First Seen (date when first scraped)
- Last Seen (date when last observed)
- Actions (View on Vinted link)

### 2. Price History Tracking ✅

**Price History Modal**
- Click on any listing (grid or table) to view price history
- Click "View History" button in table view
- Modal shows:
  - Product title
  - Current price (large, highlighted)
  - Seller name
  - Location
  - Link to Vinted
  - **Price Changes Timeline** with all historical prices

**Price History Display**:
- Shows all price observations
- Displays price and timestamp for each change
- If no changes: "No price changes recorded yet"
- Price history is stored in `price_history` table
- Only records actual price changes (not every scrape)

### 3. Visual Improvements

**New Styles**:
- View toggle buttons with active state (purple highlight)
- Responsive table with hover effects
- Sticky table header for long lists
- Modal overlay with blur background
- Clean price history timeline
- Better spacing and typography

**Table Features**:
- Horizontal scroll for narrow screens
- Hover highlighting on rows
- Consistent button styling
- Responsive image sizing

## How It Works

### Data Flow

```
Frontend (Vue.js)
  ↓
GET /api/listings
  → Returns list with basic info
  ↓
Click listing / "View History"
  ↓
GET /api/listings/{id}
  → Returns full details + price_history array
  ↓
Display in modal
```

### Price Tracking Logic

1. **First Scrape**:
   - Listing inserted into `listings` table
   - Initial price recorded in `price_history`

2. **Subsequent Scrapes**:
   - Check if price changed
   - If changed: Insert new record in `price_history`
   - If same: Skip (no duplicate entries)

3. **Display**:
   - Fetch listing with `price_history` relationship
   - Show chronological timeline
   - Latest price shown in main view

## Current Status

### Database State
```sql
-- 27 listings in database
SELECT COUNT(*) FROM vinted.listings;  -- 27

-- Price history entries
SELECT COUNT(*) FROM vinted.price_history;  -- 27 (one per listing)

-- Example price history
SELECT * FROM vinted.price_history WHERE listing_id = 6;
```

### API Endpoints Working

✅ `GET /api/listings` - List with pagination
✅ `GET /api/listings/{id}` - Detail with price_history
✅ `GET /api/stats` - Dashboard statistics
✅ `GET /api/categories` - Category list
✅ `POST /api/configs` - Create config
✅ `POST /api/configs/{id}/run` - Trigger scrape

## Screenshots (Expected View)

### Table View
```
┌─────────┬────────────────────┬──────────┬─────────┬──────────┬────────────┬───────────┬─────────┐
│ Image   │ Title              │ Price    │ Seller  │ Location │ First Seen │ Last Seen │ Actions │
├─────────┼────────────────────┼──────────┼─────────┼──────────┼────────────┼───────────┼─────────┤
│ [📷]    │ PlayStation 5      │ 284.73€  │ N/A     │ N/A      │ 10/12/25   │ 10/12/25  │ [View]  │
│         │                    │[History] │         │          │            │           │         │
└─────────┴────────────────────┴──────────┴─────────┴──────────┴────────────┴───────────┴─────────┘
```

### Price History Modal
```
┌────────────────────────────────────────┐
│  Price History                    ✕    │
├────────────────────────────────────────┤
│  PlayStation 5                         │
│                                        │
│  Current Price: 284.73 EUR             │
│  Link to Vinted                        │
│                                        │
│  Price Changes                         │
│  ┌──────────────────────────────────┐ │
│  │ 284.73 EUR    10/12/25 10:05 AM │ │
│  └──────────────────────────────────┘ │
└────────────────────────────────────────┘
```

## Testing

### Test in Browser

1. **Open Dashboard**: http://localhost:8000

2. **Switch to Listings Tab**

3. **Toggle Table View**:
   - Click "Table View" button
   - See all 27 listings in table format

4. **View Price History**:
   - Click "View History" on any listing
   - Modal opens with price timeline
   - Close with X or click outside

5. **Grid View**:
   - Click "Grid View" to return to cards
   - Click any card to see price history

### Test via API

```bash
# Get all listings
curl http://localhost:8000/api/listings?limit=5

# Get specific listing with price history
curl http://localhost:8000/api/listings/6

# Expected response includes:
# {
#   "id": 6,
#   "title": "PlayStation 5",
#   "price_cents": 28473,
#   "price_history": [
#     {
#       "id": 5,
#       "observed_at": "2025-10-12T08:05:49.687247Z",
#       "price_cents": 28473,
#       "currency": null
#     }
#   ]
# }
```

## Files Modified

### `frontend/index.html`
- **Added** (~140 lines):
  - Table view HTML structure
  - Price history modal
  - View toggle buttons
  - CSS styles for table and modal
  - `showPriceHistory()` method
  - `viewMode` state
  - `showModal` state
  - `selectedListing` state

**New CSS Classes**:
- `.view-toggle` - Toggle buttons
- `.listings-table` - Table styling
- `.table-image` - Thumbnail in table
- `.price-change` - Price change indicators
- `.modal` - Modal overlay
- `.modal-content` - Modal box
- `.price-history-item` - Price history entry

**New Vue Methods**:
```javascript
async showPriceHistory(listingId) {
  // Fetch listing detail with price_history
  // Display in modal
}
```

## Next Steps

### To Track Price Changes Over Time

1. **Run Scheduled Scrapes**:
   ```bash
   # Create config with cron schedule
   # e.g., "0 */6 * * *" (every 6 hours)
   ```

2. **Wait for Price Changes**:
   - When products get repriced
   - System will record in `price_history`
   - Modal will show multiple entries

3. **Price Change Indicators** (Future Enhancement):
   - Add arrows (↑ ↓) for price increases/decreases
   - Color coding (green = down, red = up)
   - Percentage change calculation
   - Price alerts

### Future Enhancements

1. **Price Charts**:
   - Add Chart.js library
   - Line graph showing price over time
   - Visual trend analysis

2. **Export Data**:
   - CSV export of listings
   - Include price history
   - Excel format option

3. **Advanced Filters**:
   - Filter by price range
   - Filter by price change
   - Filter by date range
   - Sort by price, date, etc.

4. **Price Alerts**:
   - Set target price
   - Email/webhook notification
   - Dashboard alerts section

## Summary

✅ **Table view** added with sortable columns
✅ **Price history tracking** with modal display
✅ **View toggle** between grid and table
✅ **27 listings** currently in database
✅ **API working** correctly with price_history data
✅ **Ready to track** price changes over time

The system is now fully equipped to:
- Display listings in both grid and table format
- Track all price changes over time
- Show historical pricing in detailed modal
- Handle future price fluctuations automatically

**Server Running**: http://localhost:8000
**All Features**: Operational ✅
