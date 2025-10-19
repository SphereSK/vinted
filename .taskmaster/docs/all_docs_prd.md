--- /home/datament/project/vinted/AGENTS.md ---

# Task Master AI - Agent Integration Guide

## Essential Commands

### Core Workflow Commands

```bash
# Project Setup
task-master init                                    # Initialize Task Master in current project
task-master parse-prd .taskmaster/docs/prd.txt      # Generate tasks from PRD document
task-master models --setup                        # Configure AI models interactively

# Daily Development Workflow
task-master list                                   # Show all tasks with status
task-master next                                   # Get next available task to work on
task-master show <id>                             # View detailed task information (e.g., task-master show 1.2)
task-master set-status --id=<id> --status=done    # Mark task complete

# Task Management
task-master add-task --prompt="description" --research        # Add new task with AI assistance
task-master expand --id=<id> --research --force              # Break task into subtasks
task-master update-task --id=<id> --prompt="changes"         # Update specific task
task-master update --from=<id> --prompt="changes"            # Update multiple tasks from ID onwards
task-master update-subtask --id=<id> --prompt="notes"        # Add implementation notes to subtask

# Analysis & Planning
task-master analyze-complexity --research          # Analyze task complexity
task-master complexity-report                      # View complexity analysis
task-master expand --all --research               # Expand all eligible tasks

# Dependencies & Organization
task-master add-dependency --id=<id> --depends-on=<id>       # Add task dependency
task-master move --from=<id> --to=<id>                       # Reorganize task hierarchy
task-master validate-dependencies                            # Check for dependency issues
task-master generate                                         # Update task markdown files (usually auto-called)
```

## Key Files & Project Structure

### Core Files

- `.taskmaster/tasks/tasks.json` - Main task data file (auto-managed)
- `.taskmaster/config.json` - AI model configuration (use `task-master models` to modify)
- `.taskmaster/docs/prd.txt` - Product Requirements Document for parsing
- `.taskmaster/tasks/*.txt` - Individual task files (auto-generated from tasks.json)
- `.env` - API keys for CLI usage

### Claude Code Integration Files

- `CLAUDE.md` - Auto-loaded context for Claude Code (this file)
- `.claude/settings.json` - Claude Code tool allowlist and preferences
- `.claude/commands/` - Custom slash commands for repeated workflows
- `.mcp.json` - MCP server configuration (project-specific)

### Directory Structure

```
project/
├── .taskmaster/
│   ├── tasks/              # Task files directory
│   │   ├── tasks.json      # Main task database
│   │   ├── task-1.md      # Individual task files
│   │   └── task-2.md
│   ├── docs/              # Documentation directory
│   │   ├── prd.txt        # Product requirements
│   ├── reports/           # Analysis reports directory
│   │   └── task-complexity-report.json
│   ├── templates/         # Template files
│   │   └── example_prd.txt  # Example PRD template
│   └── config.json        # AI models & settings
├── .claude/
│   ├── settings.json      # Claude Code configuration
│   └── commands/         # Custom slash commands
├── .env                  # API keys
├── .mcp.json            # MCP configuration
└── CLAUDE.md            # This file - auto-loaded by Claude Code
```

## MCP Integration

Task Master provides an MCP server that Claude Code can connect to. Configure in `.mcp.json`:

```json
{
  "mcpServers": {
    "task-master-ai": {
      "command": "npx",
      "args": ["-y", "task-master-ai"],
      "env": {
        "ANTHROPIC_API_KEY": "your_key_here",
        "PERPLEXITY_API_KEY": "your_key_here",
        "OPENAI_API_KEY": "OPENAI_API_KEY_HERE",
        "GOOGLE_API_KEY": "GOOGLE_API_KEY_HERE",
        "XAI_API_KEY": "XAI_API_KEY_HERE",
        "OPENROUTER_API_KEY": "OPENROUTER_API_KEY_HERE",
        "MISTRAL_API_KEY": "MISTRAL_API_KEY_HERE",
        "AZURE_OPENAI_API_KEY": "AZURE_OPENAI_API_KEY_HERE",
        "OLLAMA_API_KEY": "OLLAMA_API_KEY_HERE"
      }
    }
  }
}
```

### Essential MCP Tools

```javascript
help; // = shows available taskmaster commands
// Project setup
initialize_project; // = task-master init
parse_prd; // = task-master parse-prd

// Daily workflow
get_tasks; // = task-master list
next_task; // = task-master next
get_task; // = task-master show <id>
set_task_status; // = task-master set-status

// Task management
add_task; // = task-master add-task
expand_task; // = task-master expand
update_task; // = task-master update-task
update_subtask; // = task-master update-subtask
update; // = task-master update

// Analysis
analyze_project_complexity; // = task-master analyze-complexity
complexity_report; // = task-master complexity-report
```

## Claude Code Workflow Integration

### Standard Development Workflow

#### 1. Project Initialization

```bash
# Initialize Task Master
task-master init

# Create or obtain PRD, then parse it
task-master parse-prd .taskmaster/docs/prd.txt

# Analyze complexity and expand tasks
task-master analyze-complexity --research
task-master expand --all --research
```

If tasks already exist, another PRD can be parsed (with new information only!) using parse-prd with --append flag. This will add the generated tasks to the existing list of tasks..

#### 2. Daily Development Loop

```bash
# Start each session
task-master next                           # Find next available task
task-master show <id>                     # Review task details

# During implementation, check in code context into the tasks and subtasks
task-master update-subtask --id=<id> --prompt="implementation notes..."

# Complete tasks
task-master set-status --id=<id> --status=done
```

#### 3. Multi-Claude Workflows

For complex projects, use multiple Claude Code sessions:

```bash
# Terminal 1: Main implementation
cd project && claude

# Terminal 2: Testing and validation
cd project-test-worktree && claude

# Terminal 3: Documentation updates
cd project-docs-worktree && claude
```

### Custom Slash Commands

Create `.claude/commands/taskmaster-next.md`:

```markdown
Find the next available Task Master task and show its details.

Steps:

1. Run `task-master next` to get the next task
2. If a task is available, run `task-master show <id>` for full details
3. Provide a summary of what needs to be implemented
4. Suggest the first implementation step
```

Create `.claude/commands/taskmaster-complete.md`:

```markdown
Complete a Task Master task: $ARGUMENTS

Steps:

1. Review the current task with `task-master show $ARGUMENTS`
2. Verify all implementation is complete
3. Run any tests related to this task
4. Mark as complete: `task-master set-status --id=$ARGUMENTS --status=done`
5. Show the next available task with `task-master next`
```

## Tool Allowlist Recommendations

Add to `.claude/settings.json`:

```json
{
  "allowedTools": [
    "Edit",
    "Bash(task-master *)",
    "Bash(git commit:*)",
    "Bash(git add:*)",
    "Bash(npm run *)",
    "mcp__task_master_ai__*"
  ]
}
```

## Configuration & Setup

### API Keys Required

At least **one** of these API keys must be configured:

- `ANTHROPIC_API_KEY` (Claude models) - **Recommended**
- `PERPLEXITY_API_KEY` (Research features) - **Highly recommended**
- `OPENAI_API_KEY` (GPT models)
- `GOOGLE_API_KEY` (Gemini models)
- `MISTRAL_API_KEY` (Mistral models)
- `OPENROUTER_API_KEY` (Multiple models)
- `XAI_API_KEY` (Grok models)

An API key is required for any provider used across any of the 3 roles defined in the `models` command.

### Model Configuration

```bash
# Interactive setup (recommended)
task-master models --setup

# Set specific models
task-master models --set-main claude-3-5-sonnet-20241022
task-master models --set-research perplexity-llama-3.1-sonar-large-128k-online
task-master models --set-fallback gpt-4o-mini
```

## Task Structure & IDs

### Task ID Format

- Main tasks: `1`, `2`, `3`, etc.
- Subtasks: `1.1`, `1.2`, `2.1`, etc.
- Sub-subtasks: `1.1.1`, `1.1.2`, etc.

### Task Status Values

- `pending` - Ready to work on
- `in-progress` - Currently being worked on
- `done` - Completed and verified
- `deferred` - Postponed
- `cancelled` - No longer needed
- `blocked` - Waiting on external factors

### Task Fields

```json
{
  "id": "1.2",
  "title": "Implement user authentication",
  "description": "Set up JWT-based auth system",
  "status": "pending",
  "priority": "high",
  "dependencies": ["1.1"],
  "details": "Use bcrypt for hashing, JWT for tokens...",
  "testStrategy": "Unit tests for auth functions, integration tests for login flow",
  "subtasks": []
}
```

## Claude Code Best Practices with Task Master

### Context Management

- Use `/clear` between different tasks to maintain focus
- This CLAUDE.md file is automatically loaded for context
- Use `task-master show <id>` to pull specific task context when needed

### Iterative Implementation

1. `task-master show <subtask-id>` - Understand requirements
2. Explore codebase and plan implementation
3. `task-master update-subtask --id=<id> --prompt="detailed plan"` - Log plan
4. `task-master set-status --id=<id> --status=in-progress` - Start work
5. Implement code following logged plan
6. `task-master update-subtask --id=<id> --prompt="what worked/didn't work"` - Log progress
7. `task-master set-status --id=<id> --status=done` - Complete task

### Complex Workflows with Checklists

For large migrations or multi-step processes:

1. Create a markdown PRD file describing the new changes: `touch task-migration-checklist.md` (prds can be .txt or .md)
2. Use Taskmaster to parse the new prd with `task-master parse-prd --append` (also available in MCP)
3. Use Taskmaster to expand the newly generated tasks into subtasks. Consdier using `analyze-complexity` with the correct --to and --from IDs (the new ids) to identify the ideal subtask amounts for each task. Then expand them.
4. Work through items systematically, checking them off as completed
5. Use `task-master update-subtask` to log progress on each task/subtask and/or updating/researching them before/during implementation if getting stuck

### Git Integration

Task Master works well with `gh` CLI:

```bash
# Create PR for completed task
gh pr create --title "Complete task 1.2: User authentication" --body "Implements JWT auth system as specified in task 1.2"

# Reference task in commits
git commit -m "feat: implement JWT auth (task 1.2)"
```

### Parallel Development with Git Worktrees

```bash
# Create worktrees for parallel task development
git worktree add ../project-auth feature/auth-system
git worktree add ../project-api feature/api-refactor

# Run Claude Code in each worktree
cd ../project-auth && claude    # Terminal 1: Auth work
cd ../project-api && claude     # Terminal 2: API work
```

## Troubleshooting

### AI Commands Failing

```bash
# Check API keys are configured
cat .env                           # For CLI usage

# Verify model configuration
task-master models

# Test with different model
task-master models --set-fallback gpt-4o-mini
```

### MCP Connection Issues

- Check `.mcp.json` configuration
- Verify Node.js installation
- Use `--mcp-debug` flag when starting Claude Code
- Use CLI as fallback if MCP unavailable

### Task File Sync Issues

```bash
# Regenerate task files from tasks.json
task-master generate

# Fix dependency issues
task-master fix-dependencies
```

DO NOT RE-INITIALIZE. That will not do anything beyond re-adding the same Taskmaster core files.

## Important Notes

### AI-Powered Operations

These commands make AI calls and may take up to a minute:

- `parse_prd` / `task-master parse-prd`
- `analyze_project_complexity` / `task-master analyze-complexity`
- `expand_task` / `task-master expand`
- `expand_all` / `task-master expand --all`
- `add_task` / `task-master add-task`
- `update` / `task-master update`
- `update_task` / `task-master update-task`
- `update_subtask` / `task-master update-subtask`

### File Management

- Never manually edit `tasks.json` - use commands instead
- Never manually edit `.taskmaster/config.json` - use `task-master models`
- Task markdown files in `tasks/` are auto-generated
- Run `task-master generate` after manual changes to tasks.json

### Claude Code Session Management

- Use `/clear` frequently to maintain focused context
- Create custom slash commands for repeated Task Master workflows
- Configure tool allowlist to streamline permissions
- Use headless mode for automation: `claude -p "task-master next"`

### Multi-Task Updates

- Use `update --from=<id>` to update multiple future tasks
- Use `update-task --id=<id>` for single task updates
- Use `update-subtask --id=<id>` for implementation logging

### Research Mode

- Add `--research` flag for research-based AI enhancement
- Requires a research model API key like Perplexity (`PERPLEXITY_API_KEY`) in environment
- Provides more informed task creation and updates
- Recommended for complex technical tasks

---

_This guide ensures Claude Code has immediate access to Task Master's essential functionality for agentic development workflows.


---

--- /home/datament/project/vinted/CLAUDE.md ---

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
3. Extracts language from HTML `<html lang="..."` tag
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
5. **Automatic 403 Retry** - Waits configurable time (default 30 min) and retries on rate limits
6. **Browser Fallback** - Falls back to Playwright if warmup fails (experimental)

**Note**: Proxy rotation has been deprecated in favor of direct connections with proper cookies.

### 403 Error Handling

When Vinted returns 403 (Forbidden) errors, the scraper automatically:
- Detects the error
- Waits a configurable period (default: 30 minutes)
- Shows countdown timer with progress updates
- Retries the failed page
- Continues with next page after max retries (default: 3)

**CLI Parameters**:
```bash
--error-wait INTEGER    # Minutes to wait (default: 30)
--max-retries INTEGER   # Max retry attempts (default: 3)
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
  -c 3026 \
  --fetch-details \
  --no-proxy \
  --max-pages 10

# Query database for English listings
psql $DATABASE_URL -c "
SELECT title, description, language, price_cents/100.0 as price_eur
FROM vinted.listings
WHERE language = 'en'
  AND is_active = true
ORDER BY last_seen_at DESC;
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
**Last Updated**: 2025-10-14
**Documentation**: See `DATA_FIELDS_GUIDE.md` and `SCRAPER_BEHAVIOR.md`

## Recent Changes

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


---

--- /home/datament/project/vinted/DATA_FIELDS_GUIDE.md ---

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

1. **Location** - Not available in catalog API, requires browser automation
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


---

--- /home/datament/project/vinted/HELP_REFERENCE.md ---

# Complete Help Reference

This document shows what users see in all help commands.

## `vinted-scraper --help` (Main Help)

Shows:
1. **Quick Start** - 3 copy-paste examples
2. **ALL SCRAPE OPTIONS** - Complete flag reference with descriptions
3. **What Data is Captured** - Field availability
4. **Commands** - All available commands
5. **Web Dashboard** - How to access
6. **More Help** - Links to detailed help

### Output Structure:
```
🛒 Vinted Scraper - Track prices and listings

╔═══════════════════════════════════╗
║         QUICK START               ║
╚═══════════════════════════════════╝
[3 examples]

╔═══════════════════════════════════╗
║    ALL SCRAPE OPTIONS             ║
╚═══════════════════════════════════╝
REQUIRED:
  --search-text TEXT          [description]

FILTERING OPTIONS:
  -c, --category INTEGER      [description with examples]
  -p, --platform-id INTEGER   [description with examples]
  -e, --extra TEXT            [description with examples]

SCRAPING CONTROL:
  --max-pages INTEGER         [description + default]
  --per-page INTEGER          [description + default]
  --delay FLOAT               [description + default]
  --no-proxy                  [description + recommendation]

DETAIL FETCHING:
  --fetch-details             [description + warning]
  --details-for-new-only      [description + recommendation]

REGION OPTIONS:
  --base-url TEXT             [description + examples]
  --locale TEXT               [description + examples]

╔═══════════════════════════════════╗
║    WHAT DATA IS CAPTURED          ║
╚═══════════════════════════════════╝
[Lists all fields by category]

╔═══════════════════════════════════╗
║         COMMANDS                  ║
╚═══════════════════════════════════╝
[Auto-generated by Typer]

╔═══════════════════════════════════╗
║      WEB DASHBOARD                ║
╚═══════════════════════════════════╝
[How to start and access]

╔═══════════════════════════════════╗
║        MORE HELP                  ║
╚═══════════════════════════════════╝
[Links to other help commands]
```

## `vinted-scraper scrape --help` (Detailed Scrape Help)

Shows the full **Options** section with ALL flags described in detail:

### Options Section:
```
╭─ Options ──────────────────────────────────────────────────╮
│ *  --search-text       TEXT     🔍 [REQUIRED] Search      │
│                                 query (e.g., 'ps5')       │
│                                 [required]                │
│                                                           │
│    -c                  INTEGER  📂 Category ID(s) to      │
│                                 filter by (repeatable).   │
│                                 Example: -c 3026 for      │
│                                 Video Games. List all:    │
│                                 vinted-scraper categories │
│                                                           │
│    -p                  INTEGER  🎮 Video game platform    │
│                                 ID(s) (repeatable).       │
│                                 Example: -p 1281 (PS5),   │
│                                 -p 1280 (PS4). List all:  │
│                                 vinted-scraper platforms  │
│                                                           │
│    -e                  TEXT     ➕ Extra query params as  │
│                                 key=value pairs.          │
│                                 Example: -e 'price_to=100'│
│                                                           │
│    --max-pages         INTEGER  📄 Pages to scrape        │
│                                 [default: 5] (24/page).   │
│                                 Note: Pages may contain   │
│                                 duplicates, so 5 pages ≠  │
│                                 120 unique items          │
│                                 [default: 5]              │
│                                                           │
│    --per-page          INTEGER  📊 Items per page         │
│                                 [default: 24] (max: 24)   │
│                                 [default: 24]             │
│                                                           │
│    --delay             FLOAT    ⏱️  Delay in seconds      │
│                                 between requests          │
│                                 [default: 1.0] (min: 0.5).│
│                                 Increase if rate limits   │
│                                 [default: 1.0]            │
│                                                           │
│    --base-url          TEXT     🌍 Base Vinted URL        │
│                                 [default: vinted.sk].     │
│                                 Examples: vinted.com,     │
│                                 vinted.fr, vinted.pl      │
│                                 [default:                 │
│                                 https://vinted.sk/catalog]│
│                                                           │
│    --locale            TEXT     🗣️  Locale code           │
│                                 [default: sk].            │
│                                 Examples: en, fr, de, pl  │
│                                 [default: sk]             │
│                                                           │
│    --fetch-details              📝 Fetch HTML details for │
│                                 ALL items (description,   │
│                                 language, photos).        │
│                                 ⚠️  WARNING: 3x slower     │
│                                 (~10 items/min vs 24).    │
│                                 Gets: description,        │
│                                 language, photos, shipping│
│                                                           │
│    --details-for-new-only       📝 Fetch details ONLY for │
│                                 new listings              │
│                                 (recommended). Faster than│
│                                 --fetch-details.          │
│                                 Auto-enables HTML fetching│
│                                                           │
│    --no-proxy                   ⚡ Skip proxy and connect │
│                                 directly [RECOMMENDED].   │
│                                 Faster and more reliable. │
│                                 Use this in production!   │
│                                                           │
│    --help                       Show this message         │
╰───────────────────────────────────────────────────────────╯
```

## `vinted-scraper examples` (30+ Examples)

Shows 9 sections:

1. **Basic Scraping** - Simple searches
2. **Platform Filtering** - PS5, PS4, Nintendo, etc.
3. **With Descriptions** - English filtering
4. **Advanced Options** - Delay, region, extras
5. **Production Use Cases** - Daily tracking
6. **Common Flag Reference** - Complete table
7. **Helper Commands** - categories, platforms
8. **What Data is Captured** - Field lists
9. **Web Dashboard** - UI features

## `vinted-scraper categories` / `platforms`

Shows:
- List of all IDs with names
- Search functionality with `--search`
- Usage examples

## Summary of What's Visible

### ✅ In Main Help (`--help`):
- Quick start examples
- **ALL OPTIONS** with descriptions
- Data availability info
- Commands list
- Web dashboard info
- Links to more help

### ✅ In Scrape Help (`scrape --help`):
- **Detailed Options section** with:
  - Emojis for visual identification
  - Full descriptions
  - Examples for each option
  - Default values shown
  - Warnings where needed (--fetch-details)
  - Recommendations where needed (--no-proxy)
- Data captured info
- Quick examples
- Links to dashboard

### ✅ In Examples Command:
- 30+ copy-paste ready examples
- Organized by use case
- All flag combinations shown

## Quick Reference Table

| Flag | Short | Description | Default |
|------|-------|-------------|---------|
| `--search-text` | - | 🔍 Search query | Required |
| `--category` | `-c` | 📂 Category ID | None |
| `--platform-id` | `-p` | 🎮 Platform ID | None |
| `--extra` | `-e` | ➕ Extra params | None |
| `--max-pages` | - | 📄 Pages to scrape | 5 |
| `--per-page` | - | 📊 Items per page | 24 |
| `--delay` | - | ⏱️  Request delay | 1.0 |
| `--base-url` | - | 🌍 Vinted URL | vinted.sk |
| `--locale` | - | 🗣️  Locale code | sk |
| `--fetch-details` | - | 📝 Get HTML (slow) | False |
| `--details-for-new-only` | - | 📝 Get HTML for new | False |
| `--no-proxy` | - | ⚡ Direct connect | False |

## Test All Help Commands

```bash
# Main help - shows everything
vinted-scraper --help

# Detailed options
vinted-scraper scrape --help

# 30+ examples
vinted-scraper examples

# Helper commands
vinted-scraper categories
vinted-scraper categories --search "video"
vinted-scraper platforms
vinted-scraper platforms --search "playstation"
```


---

--- /home/datament/project/vinted/PLATFORM_SUPPORT.md ---

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
  -p 1280
```

**Integration Points**:
- Automatically syncs when creating config with schedule
- Automatically syncs when deleting config
- Manual sync via API: `POST /api/cron/sync`

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

**Now you can filter video game listings by specific platforms!

---

*Last Updated: 2025-10-12*
*Server: http://localhost:8000


---

--- /home/datament/project/vinted/PRD.md ---

# Product Requirements Document: Vinted Scraper Extensions

## 1. Overview

This document outlines the requirements for extending the Vinted Scraper application with new features to improve its reliability, flexibility, and data quality.

## 2. Goals

*   To improve the reliability of the scraper by implementing a more robust detail fetching mechanism.
*   To make the scraper more resilient to errors and network issues.
*   To extend the scraper's functionality to support more Vinted locales.
*   To improve the quality of the scraped data by adding a data cleaning and normalization pipeline.

## 3. Features

### 3.1. Full Browser Automation for Details

*   **User Story:** As a user, I want the scraper to reliably fetch detailed information for each listing, even when faced with anti-bot measures like Cloudflare, so that I can get complete and accurate data.
*   **Requirements:**
    *   Integrate a headless browser solution (e.g., `undetected_chromedriver`) to fetch the full HTML of listing detail pages.
    *   Replace the current `requests`-based detail fetching with the new browser-based implementation.
    *   Ensure that the browser-based implementation is efficient and does not significantly slow down the scraping process.
*   **Success Metrics:**
    *   A significant reduction in the number of failed detail fetches.
    *   The ability to consistently scrape detailed information (description, all photos, etc.) for all listings.

### 3.2. Improved Error Handling and Resilience

*   **User Story:** As a user, I want the scraper to be more resilient to errors and network issues, so that it can continue scraping even when it encounters temporary problems.
*   **Requirements:**
    *   Implement more specific error handling for different types of exceptions (e.g., network errors, parsing errors, database errors).
    *   Implement a more sophisticated retry mechanism with exponential backoff for handling temporary network problems.
*   **Success Metrics:**
    *   A reduction in the number of scraper failures due to temporary errors.
    *   The ability of the scraper to automatically recover from temporary errors and continue its work.

### 3.3. Support for More Vinted Locales

*   **User Story:** As a user, I want to be able to scrape listings from different Vinted locales, so that I can collect data from multiple countries.
*   **Requirements:**
    *   Refactor the code to allow the Vinted locale to be a configurable option.
    *   Handle any differences in the website structure or API endpoints for different locales.
*   **Success Metrics:**
    *   The ability to successfully scrape listings from at least three different Vinted locales (e.g., `sk`, `com`, `fr`).

### 3.4. Data Cleaning and Normalization

*   **User Story:** As a user, I want the scraped data to be clean and normalized, so that I can easily analyze and use it.
*   **Requirements:**
    *   Add a data processing pipeline to clean and normalize the scraped data.
    *   Standardize brand names (e.g., "Sony" and "sony" become the same).
    *   Convert sizes to a consistent format.
    *   Parse more structured data from the descriptions.
*   **Success Metrics:**
    *   A noticeable improvement in the quality and consistency of the scraped data.
    *   The ability to perform more accurate analysis on the scraped data.


---

--- /home/datament/project/vinted/PROJECT_SUMMARY.md ---

# Vinted Scraper Project - Complete Implementation Summary

## Project Overview

Built a comprehensive web-based product scraping system for Vinted marketplace with automated price tracking, scheduled scraping, and multi-supplier comparison capabilities.

---

## What Was Done

### Phase 1: Core Improvements

#### 1.1 Removed Proxy Dependencies
**Problem**: Complex proxy rotation was causing failures and cookie management issues.

**Solution**:
- Removed all proxy-related code from `app/ingest.py`
- Switched to direct connections with proper headers
- Simplified to header-based anti-bot strategy
- Session warmup still captures Cloudflare cookies naturally

**Files Modified**:
- `app/ingest.py` - Removed proxy logic, simplified to direct connections
- Imports cleaned up (removed `get_working_proxy`, `os`, `json`)

#### 1.2 Added Category Discovery Command
**Feature**: CLI command to list and search available Vinted categories.

**Implementation**:
```bash
# List all categories
vinted-scraper categories

# Search for specific categories
vinted-scraper categories --search "game"
```

**Files Created**:
- `app/utils/categories.py` - Category management functions
  - `COMMON_CATEGORIES` - Dictionary of category IDs and names
  - `list_common_categories()` - Get all categories
  - `search_categories(query)` - Search by name
  - `get_category_name(id)` - Get name by ID

**Files Modified**:
- `app/cli.py` - Added `categories` command with search option

**Categories Available**:
```
Electronics & Gaming:
  2994 - Electronics
  3026 - Video Games
  1953 - Computers

Fashion:
    16 - Women's Clothing
    18 - Men's Clothing
    12 - Kids & Baby

Home & Lifestyle:
  1243 - Home
     5 - Entertainment
```

#### 1.3 Added Progress Tracking
**Feature**: Real-time progress display with time estimates during scraping.

**Implementation**:
- Page progress: `Page 5/23`
- Items scraped: `120 items`
- Time tracking: `5m 32s elapsed, ~15m 20s remaining`
- Per-page stats: `✓ Page 5 complete: 24 items in 12.3s`
- Final summary: `✅ Done. Processed 576 listings in 23m 45s`

**Files Modified**:
- `app/ingest.py`:
  - Added `import time` for timing
  - Added `start_time`, `page_times[]` tracking
  - Calculate average page time and ETA
  - Display progress on each page
  - Show per-page completion stats
  - Final summary with total time

**Code Added**:
```python
# Track timing
start_time = time.time()
page_times = []

# Calculate ETA
if page > 1 and page_times:
    avg_page_time = sum(page_times) / len(page_times)
    remaining_pages = max_pages - page + 1
    eta_seconds = avg_page_time * remaining_pages
    # Display: "[120 items, 5m 32s elapsed, ~15m 20s remaining]"
```

---

### Phase 2: Web Dashboard Implementation

#### 2.1 Database Schema Extensions
**Feature**: Added scrape configuration storage for automated scheduling.

**New Model** (`app/db/models.py`):
```python
class ScrapeConfig(Base):
    __tablename__ = "scrape_configs"

    # Configuration
    id, name, search_text
    categories (JSON), platform_ids (JSON)

    # Parameters
    max_pages, per_page, delay
    fetch_details (bool)

    # Scheduling
    cron_schedule, is_active

    # Status tracking
    created_at, last_run_at
    last_run_status, last_run_items
```

**Database Created**:
```sql
CREATE TABLE vinted.scrape_configs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    search_text VARCHAR(256) NOT NULL,
    categories JSON,
    platform_ids JSON,
    max_pages INTEGER DEFAULT 5,
    per_page INTEGER DEFAULT 24,
    delay NUMERIC(5,2) DEFAULT 1.0,
    fetch_details BOOLEAN DEFAULT FALSE,
    cron_schedule VARCHAR(128),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_run_at TIMESTAMP WITH TIME ZONE,
    last_run_status VARCHAR(64),
    last_run_items INTEGER
);

CREATE INDEX ix_scrape_configs_active ON vinted.scrape_configs(is_active);
```

#### 2.2 FastAPI Backend
**Feature**: Complete REST API for web interface.

**Files Created**:
- `app/api/__init__.py`
- `app/api/schemas.py` - Pydantic models for request/response validation
- `app/api/main.py` - FastAPI application with all endpoints

**API Endpoints Implemented**:

##### Listings
- `GET /api/listings` - List with pagination, search, filtering
  - Query params: `skip`, `limit`, `search`, `active_only`
  - Returns: Array of `ListingResponse`
- `GET /api/listings/{id}` - Detail view with price history
  - Returns: `ListingDetail` with price history array

##### Configurations
- `GET /api/configs` - List all configurations
  - Query: `active_only` filter
- `POST /api/configs` - Create new configuration
  - Body: `ScrapeConfigCreate` (name, search_text, categories, etc.)
  - Auto-syncs to crontab if schedule set
- `GET /api/configs/{id}` - Get single configuration
- `PUT /api/configs/{id}` - Update configuration
  - Body: `ScrapeConfigUpdate` (partial updates)
- `DELETE /api/configs/{id}` - Delete configuration
  - Auto-syncs crontab after deletion
- `POST /api/configs/{id}/run` - Trigger immediate scrape
  - Runs in background, updates status

##### Categories
- `GET /api/categories` - List all available categories
  - Returns: Array of `{id, name}`

##### Statistics
- `GET /api/stats` - Dashboard statistics
  - Returns:
    ```json
    {
      "total_listings": 27,
      "active_listings": 27,
      "total_scraped_today": 27,
      "active_configs": 0,
      "avg_price_cents": 22524.70
    }
    ```

##### Cron Management
- `GET /api/cron/jobs` - List scheduled cron jobs
- `POST /api/cron/sync` - Manually sync configs to crontab

##### Frontend
- `GET /` - Serve Vue.js single-page application

**Pydantic Schemas** (`app/api/schemas.py`):
```python
# Listings
ListingBase, ListingResponse, ListingDetail

# Price History
PriceHistoryResponse

# Configurations
ScrapeConfigCreate, ScrapeConfigUpdate, ScrapeConfigResponse

# Categories
CategoryResponse

# Stats
StatsResponse
```

**Features**:
- CORS middleware for cross-origin requests
- Async database session management
- Dependency injection for DB sessions
- Error handling with proper HTTP status codes
- Background task execution for scraping

#### 2.3 Cron Scheduler Integration
**Feature**: Automatic synchronization with system crontab.

**File Created**: `app/scheduler.py`

**Functions Implemented**:
```python
async def sync_crontab()
# Syncs all active configs with cron schedules to system crontab
# - Removes all existing vinted-scraper jobs
# - Reads active configs from database
# - Generates cron commands
# - Writes to system crontab

async def list_scheduled_jobs()
# Lists all vinted-scraper cron jobs

async def remove_all_jobs()
# Clears all vinted-scraper jobs from crontab
```

**CLI Usage**:
```bash
python -m app.scheduler sync   # Sync configs to crontab
python -m app.scheduler list   # List scheduled jobs
python -m app.scheduler clear  # Remove all jobs
```

**Generated Cron Commands**:
```bash
# Example output for config with schedule "0 */6 * * *"
cd /home/datament/project/vinted && vinted-scraper scrape \
  --search-text 'ps5' \
  --max-pages 10 \
  --delay 1.5 \
  -c 3026 \
  --no-proxy
```

**Integration Points**:
- Automatically syncs when creating config with schedule
- Automatically syncs when deleting config
- Manual sync via API: `POST /api/cron/sync`

#### 2.4 Vue.js Frontend
**Feature**: Single-page application for managing scraper.

**File Created**: `frontend/index.html` (self-contained, no build process)

**Technology Stack**:
- Vue.js 3 (CDN)
- Axios (CDN)
- Vanilla CSS (embedded)

**User Interface**:

##### Dashboard Tab
- **Statistics Cards**:
  - Total Listings
  - Active Listings
  - Scraped Today
  - Active Configs
  - Average Price
- Real-time data via `GET /api/stats`

##### Listings Tab
- **Search Bar**: Filter by title
- **Product Grid**: Card layout with:
  - Product image
  - Title
  - Price (formatted with currency)
  - Seller name
  - Location
  - Link to Vinted listing
- **Pagination**: "Load More" button
- **Empty State**: Message when no listings found

##### Scrape Configs Tab
- **Configuration List**: Shows all configs with:
  - Name and search text
  - Parameters (pages, delay)
  - Cron schedule
  - Last run info (timestamp, status, items)
  - Action buttons (Run Now, Delete)
- **Create Form** (toggleable):
  - Name input
  - Search text input
  - Categories input (comma-separated IDs)
  - Max pages (number)
  - Delay (seconds)
  - Cron schedule (optional)
  - Helper text showing category IDs
- **Status Badges**: Color-coded (success/running/failed)

**Vue.js App Structure**:
```javascript
createApp({
  data() {
    return {
      currentTab: 'dashboard',
      stats: {},
      listings: [],
      configs: [],
      searchQuery: '',
      newConfig: { ... }
    }
  },

  methods: {
    loadStats() { ... },
    loadListings() { ... },
    loadMoreListings() { ... },
    searchListings() { ... },
    loadConfigs() { ... },
    createConfig() { ... },
    runConfig(id) { ... },
    deleteConfig(id) { ... }
  }
})
```

**Styling**:
- Modern gradient header (purple)
- Card-based layout
- Responsive grid system
- Hover effects and transitions
- Clean color palette
- Professional status badges

---

### Phase 3: Infrastructure & Documentation

#### 3.1 Dependencies Added
**File Modified**: `pyproject.toml`

**New Dependencies**:
```toml
"fastapi"
"uvicorn[standard]"
"pydantic"
"python-crontab"
```

**Installation**:
```bash
pip install fastapi uvicorn python-crontab
```

#### 3.2 Startup Scripts
**File Created**: `start_server.sh`

```bash
#!/bin/bash
echo "🚀 Starting Vinted Scraper Dashboard..."
echo "📍 API: http://localhost:8000/api"
echo "🌐 Frontend: http://localhost:8000"

# Activate venv if exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run FastAPI server
python3 -m app.api.main
```

**Usage**:
```bash
chmod +x start_server.sh
./start_server.sh
```

#### 3.3 Documentation Created

**Files Created**:

1. **`WEBUI_README.md`** (2,500+ words)
   - Complete feature documentation
   - Quick start guide
   - API endpoint reference
   - Category IDs reference
   - Cron schedule examples
   - Database schema details
   - Troubleshooting guide
   - Architecture overview
   - Production deployment tips

2. **`SETUP_COMPLETE.md`** (1,800+ words)
   - Implementation summary
   - What was built
   - Quick start instructions
   - Current database status
   - Success metrics
   - Next steps and enhancements

3. **`PROJECT_SUMMARY.md`** (This file)
   - Complete technical documentation
   - Code changes and additions
   - Feature implementations
   - File structure

---

## Technical Architecture

### Directory Structure
```
vinted/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI app (380 lines)
│   │   └── schemas.py        # Pydantic models (110 lines)
│   ├── db/
│   │   ├── models.py         # +40 lines (ScrapeConfig model)
│   │   └── session.py
│   │   └── base.py
│   ├── scraper/
│   │   ├── parse_header.py
│   │   ├── parse_detail.py
│   │   ├── session_warmup.py
│   │   ├── session_warmup_browser.py
│   │   └── vinted_client.py
│   ├── proxies/
│   │   └── fetch_and_test.py
│   ├── utils/
│   │   ├── categories.py     # New (80 lines)
│   │   └── url.py
│   ├── cli.py                # +30 lines (categories command)
│   ├── ingest.py             # Modified (simplified proxy, added progress)
│   ├── scheduler.py          # New (110 lines)
│   └── config.py
├── frontend/
│   └── index.html            # New (620 lines)
├── migrations/
│   └── ...
├── pyproject.toml            # Modified (added deps)
└── start_server.sh           # New (executable)
├── WEBUI_README.md           # New (comprehensive docs)
├── SETUP_COMPLETE.md         # New (setup guide)
├── PROJECT_SUMMARY.md        # New (this file)
└── CLAUDE.md                 # Existing (project context)
```

### Data Flow

#### Scraping Flow
```
1. User creates ScrapeConfig via Web UI
   ↓
2. POST /api/configs → Database
   ↓
3. Auto-sync to system crontab
   ↓
4. Cron triggers: vinted-scraper scrape [params]
   ↓
5. app/ingest.py → scrape_and_store()
   ↓
6. VintedApi → Fetch items
   ↓
7. Database → Upsert Listing, PriceHistory
   ↓
8. Update ScrapeConfig status
```

#### Web UI Data Flow
```
Browser → Vue.js App → Axios
   ↓
FastAPI Endpoints
   ↓
SQLAlchemy (AsyncPG)
   ↓
PostgreSQL (via PgBouncer)
   ↓
Return JSON
   ↓
Vue.js Reactive Update → DOM
```

### Database Schema

#### Existing Tables
- **listings** (27 rows)
  - Product data, seller info, photos
  - Unique on `url`
  - Tracks `first_seen_at`, `last_seen_at`, `is_active`

- **price_history**
  - One-to-many with listings
  - Records price changes over time
  - `observed_at` timestamp

#### New Tables
- **scrape_configs** (0 rows initially)
  - Configuration storage
  - Cron schedule management
  - Status tracking

---

## Key Features Summary

### ✅ Completed Features

1. **Simplified Scraping**
   - Removed complex proxy logic
   - Direct connections with headers only
   - Session warmup for Cloudflare cookies

2. **Category Discovery**
   - CLI command: `vinted-scraper categories`
   - Search functionality
   - 8 common categories included

3. **Progress Tracking**
   - Real-time page progress
   - Elapsed/remaining time estimates
   - Per-page statistics
   - Final summary with totals

4. **Web Dashboard**
   - Beautiful Vue.js interface
   - 3 main tabs (Dashboard, Listings, Configs)
   - Real-time statistics
   - Product browser with search
   - Configuration management

5. **Automated Scheduling**
   - Cron integration
   - Automatic crontab sync
   - Manual trigger option
   - Status tracking

6. **RESTful API**
   - 15+ endpoints
   - Full CRUD for configurations
   - Statistics and monitoring
   - Cron management

7. **Multi-Supplier Ready**
   - Extensible database schema
   - Designed for multiple sources
   - Comparison views (future enhancement)

---

## How to Use

### 1. Start the Server
```bash
./start_server.sh
# Or: python3 -m app.api.main
```

### 2. Access Web UI
Open browser: **http://localhost:8000**

### 3. Create Configuration
1. Go to "Scrape Configs" tab
2. Click "+ New Configuration"
3. Fill in form:
   ```
   Name: PS5 Games Monitor
   Search Text: ps5
   Categories: 3026
   Max Pages: 10
   Delay: 1.5
   Cron Schedule: 0 */6 * * *
   ```
4. Click "Create Configuration"

### 4. Monitor Results
- Dashboard shows statistics
- Listings tab displays all products
- Config shows last run status

### 5. CLI Commands
```bash
# List categories
vinted-scraper categories

# Search categories
vinted-scraper categories --search "game"

# Manual scrape (still works)
vinted-scraper scrape --search-text "ps5" -c 3026 --max-pages 5

# Cron management
python -m app.scheduler sync
python -m app.scheduler list
```

---

## Current System State

### Database
- **Connection**: PostgreSQL via PgBouncer (port 6432)
- **Schema**: `vinted`
- **Tables**: `listings`, `price_history`, `scrape_configs`
- **Current Data**:
  - 27 listings (PS5 products)
  - Average price: 225.25 EUR
  - All scraped today

### Server
- **Status**: Running on port 8000
- **API**: http://localhost:8000/api
- **Frontend**: http://localhost:8000
- **Docs**: http://localhost:8000/docs (FastAPI auto-generated)

### Cron
- **Jobs**: 0 (no configs created yet)
- **Command**: `crontab -l | grep vinted`
- **Sync**: Automatic on config create/delete

---

## Testing the System

### 1. Test API
```bash
# Get stats
curl http://localhost:8000/api/stats | python3 -m json.tool

# Get categories
curl http://localhost:8000/api/categories | python3 -m json.tool

# Get listings
curl "http://localhost:8000/api/listings?limit=5" | python3 -m json.tool
```

### 2. Test Frontend
1. Open http://localhost:8000
2. Click through tabs
3. Search listings
4. View product details

### 3. Test Configuration
1. Create test config via UI
2. Click "Run Now"
3. Watch stats update
4. Check crontab: `crontab -l | grep vinted`

---

## Code Statistics

### Lines of Code Added/Modified

| File | Lines | Type |
|------|-------|------|
| `app/api/main.py` | 380 | New |
| `app/api/schemas.py` | 110 | New |
| `app/scheduler.py` | 110 | New |
| `app/utils/categories.py` | 80 | New |
| `frontend/index.html` | 620 | New |
| `app/db/models.py` | +40 | Modified |
| `app/cli.py` | +30 | Modified |
| `app/ingest.py` | +50, -80 | Modified |
| Documentation | 5,000+ | New |
| **Total** | **~6,420** | **Added** |

### Technologies Used
- **Backend**: Python 3.11, FastAPI, SQLAlchemy, AsyncPG
- **Frontend**: Vue.js 3, Axios, Vanilla CSS
- **Database**: PostgreSQL 14+, PgBouncer
- **Scheduler**: python-crontab, system cron
- **Scraping**: vinted-api-kit, requests
- **CLI**: Typer
- **Validation**: Pydantic

---

## Future Enhancements

### Planned Features
1. **Multi-Supplier Support**
   - Add eBay scraper
   - Add Amazon scraper
   - Unified comparison view

2. **Advanced Filtering**
   - Price range filter
   - Condition filter
   - Location-based search
   - Date range selector

3. **Alerts & Notifications**
   - Email on price drops
   - Webhook integration
   - Discord/Slack notifications

4. **Export Functionality**
   - CSV export
   - Excel export
   - PDF reports

5. **User Authentication**
   - Multi-user support
   - Role-based access
   - API keys

6. **Analytics Dashboard**
   - Price trends over time
   - Chart visualizations
   - Market insights

---

## Troubleshooting Reference

### Common Issues

#### Port 8000 Already in Use
```bash
lsof -ti:8000 | xargs kill -9
```

#### Cron Not Syncing
```bash
# Check permissions
ls -la ~/.crontab

# Manual sync
python -m app.scheduler sync

# Verify
crontab -l | grep vinted
```

#### Database Connection Issues
```bash
# Test connection
psql -h 127.0.0.1 -p 6432 -U vinted_user -d vinted_db

# Re-init database
python3 -c "from app.db.session import init_db; import asyncio; asyncio.run(init_db())"
```

#### Frontend Not Loading
```bash
# Check server logs
python3 -m app.api.main

# Check frontend file exists
ls -la frontend/index.html

# Check API response
curl http://localhost:8000/
```

---

## Security Considerations

### Current Security
- No authentication (local use only)
- CORS allows all origins
- Database credentials in `.env`
- No rate limiting

### Production Recommendations
1. Add JWT authentication
2. Restrict CORS origins
3. Use environment variables
4. Add rate limiting
5. Enable HTTPS
6. Use proper secrets management
7. Add input sanitization
8. Implement API keys

---

## Performance Considerations

### Current Performance
- Async database operations
- Background task execution for scraping
- Pagination for large datasets
- Efficient SQL queries

### Optimization Opportunities
1. Add Redis caching for stats
2. Use Celery for background tasks
3. Implement database connection pooling
4. Add CDN for static assets
5. Enable gzip compression
6. Add database indexes
7. Implement query optimization

---

## Maintenance Guide

### Daily Tasks
- Check cron logs: `tail -f /var/log/syslog | grep vinted`
- Monitor database size
- Review scraping success rates

### Weekly Tasks
- Review and archive old price history
- Check for duplicate listings
- Update category mappings

### Monthly Tasks
- Backup database
- Review system performance
- Update dependencies
- Clean up inactive configs

---

## Success Metrics

### System Health Indicators
✅ Server running on port 8000
✅ API responding correctly
✅ Frontend accessible
✅ Database connected (27 listings)
✅ Categories loaded (8 categories)
✅ Stats endpoint working
✅ No errors in logs

### Next Steps for User
1. Create first automated configuration
2. Test manual scrape via UI
3. Verify cron job was created
4. Monitor first automated run
5. Add more product categories
6. Set up price alerts (future)

---

## Project Timeline

1. **Phase 1**: Core Improvements (1-2 hours)
   - Removed proxy logic
   - Added category discovery
   - Implemented progress tracking

2. **Phase 2**: Web Dashboard (3-4 hours)
   - Built FastAPI backend
   - Created Vue.js frontend
   - Implemented cron scheduler
   - Extended database schema

3. **Phase 3**: Documentation (1 hour)
   - Created comprehensive docs
   - Wrote setup guides
   - Added troubleshooting

**Total Time**: ~6 hours of development

---

## Conclusion

The Vinted scraper has been transformed from a CLI-only tool into a fully-featured web application with:

- **Complete Web UI** for easy management
- **Automated Scheduling** via cron integration
- **Real-time Monitoring** with statistics dashboard
- **Extensible Architecture** ready for multi-supplier support
- **Comprehensive Documentation** for maintenance and enhancement

The system is production-ready for personal use and can be scaled up with authentication, caching, and additional suppliers as needed.

**Server Status**: ✅ Running at http://localhost:8000

**Current Data**: 27 PS5 listings, 0 configurations (ready to create!)


---

--- /home/datament/project/vinted/README.md ---

# Vinted Scraper

This project is a Python-based asynchronous web scraper for the Vinted marketplace. It is designed to collect data on product listings and store it in a PostgreSQL or SQLite database. The scraper is highly customizable, allowing users to specify search queries, categories, and other parameters. It also tracks price changes over time.

## Features

*   **Asynchronous Scraping:** Utilizes `asyncio` and `httpx` for efficient, non-blocking I/O operations.
*   **Database Support:** Works with both PostgreSQL and SQLite for flexible data storage.
*   **Price Tracking:** Monitors and records price changes for each listing over time.
*   **RESTful API:** A `FastAPI` backend provides endpoints for managing scrape configurations, viewing listings, and monitoring statistics.
*   **Web Dashboard:** A simple, intuitive frontend built with `Next.js` and `shadcn/ui` for interacting with the scraper and viewing data.
*   **Scheduled Scraping:** Integrated `cron` support for automated, periodic scraping tasks.
*   **Language Detection:** Automatically detects the language of listing descriptions.
*   **Proxy Support:** Supports using proxies to avoid rate limiting and IP bans.
*   **Command-Line Interface:** A powerful `Typer`-based CLI for manual scraping and administration.

## Project Structure

```
/home/datament/project/vinted/
├───app/
│   ├───api/
│   │   ├───main.py         # FastAPI application
│   │   └───schemas.py      # Pydantic schemas for API
│   ├───db/
│   │   ├───models.py       # SQLAlchemy ORM models
│   │   └───session.py      # Database session management
│   ├───scraper/
│   │   ├───vinted_client.py # Core scraping logic
│   │   └───...
│   ├───cli.py              # Typer CLI application
│   ├───ingest.py           # Data ingestion and processing
│   └───...
├───frontend/
│   └───index.html          # Web dashboard
├───migrations/
│   └───...
├───pyproject.toml          # Project dependencies
└───README.md
```

## Getting Started

### Prerequisites

*   Python 3.9+
*   `pip` and `venv`

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/vinted-scraper.git
    cd vinted-scraper
    ```

2.  **Create a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -e .
    ```

4.  **Configure environment variables:**
    Create a `.env` file in the project root, based on the `.env.example` file. Customize the `DATABASE_URL` and other settings as needed.

    ```
    # .env
    DATABASE_URL=sqlite+aiosqlite:///./vinted.db
    # or for PostgreSQL:
    # DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname
    ```

5.  **Initialize the database:**
    The database schema is created automatically when the application starts.

### Running the Application

You can run the scraper in two ways:

1.  **Web Dashboard (Recommended):**
    Start the FastAPI server:
    ```bash
    uvicorn app.api.main:app --reload
    ```
    Open your browser and navigate to `http://localhost:8000`.

2.  **Command-Line Interface:**
    Use the `vinted-scraper` command for manual scraping and administration.
    ```bash
    vinted-scraper scrape --search-text "ps5" --max-pages 10
    ```

## Command-Line Interface

The `vinted-scraper` CLI provides a comprehensive set of commands for managing the scraper.

### `scrape`

Scrape Vinted listings and save them to the database.

**Usage:**
```bash
vinted-scraper scrape [OPTIONS]
```

**Common Options:**
*   `--search-text`: The search query.
*   `-c`, `--category`: Filter by category ID.
*   `-p`, `--platform-id`: Filter by video game platform ID.
*   `--max-pages`: The number of pages to scrape.
*   `--fetch-details`: Fetch detailed information for each listing (slower).
*   `--no-proxy`: Disable proxy usage (recommended for reliability).

For a full list of options, run:
```bash
vinted-scraper scrape --help
```

### `categories`

List available Vinted categories.

**Usage:**
```bash
vinted-scraper categories
```

### `platforms`

List available video game platforms.

**Usage:**
```bash
vinted-scraper platforms
```

## API Documentation

The FastAPI backend provides the following endpoints:

*   `GET /api/listings`: Get a list of scraped listings.
*   `GET /api/listings/{listing_id}`: Get details for a specific listing.
*   `GET /api/configs`: Get all scrape configurations.
*   `POST /api/configs`: Create a new scrape configuration.
*   `PUT /api/configs/{config_id}`: Update a scrape configuration.
*   `DELETE /api/configs/{config_id}`: Delete a scrape configuration.
*   `POST /api/configs/{config_id}/run`: Manually trigger a scrape.
*   `GET /api/stats`: Get dashboard statistics.
*   `GET /api/categories`: Get available categories.
*   `GET /api/platforms`: Get available video game platforms.

For interactive API documentation, visit `http://localhost:8000/docs` when the server is running.

## Web Dashboard

**Note:** The current frontend is a placeholder. The intended frontend is a `Next.js` application with `shadcn/ui`.

The web dashboard provides a user-friendly interface for:

*   Viewing and searching listings.
*   Creating and managing scrape configurations.
*   Scheduling automated scrapes with `cron`.
*   Monitoring price changes and statistics.

To access the dashboard, start the API server and visit `http://localhost:8000`.

## Database Schema

The database schema consists of three main tables:

*   `listings`: Stores the core information for each scraped listing.
*   `price_history`: Tracks the price of each listing over time.
*   `scrape_configs`: Stores user-defined configurations for scraping tasks.

The schema is defined in `app/db/models.py` using SQLAlchemy ORM.

## Frontend Development

### Schema-Driven Approach (tRPC + Zod)

The frontend will be developed using a schema-driven approach with `tRPC` and `Zod`. This provides end-to-end type safety between the backend and frontend, ensuring that the API requests and responses are always in sync.

*   **`Zod`** will be used to define the validation schemas for the API data.
*   **`tRPC`** will be used to create a type-safe API layer, allowing the frontend to call backend procedures as if they were local functions.

This approach eliminates the need for manual API documentation and reduces the risk of runtime errors due to mismatched types.


---
