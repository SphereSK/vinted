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