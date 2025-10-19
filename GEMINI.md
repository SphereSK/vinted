# Vinted Scraper

## Project Overview

This project is a Python-based asynchronous web scraper for the Vinted marketplace. It is designed to collect data on product listings and store it in a PostgreSQL or SQLite database. The scraper is highly customizable, allowing users to specify search queries, categories, and other parameters. It also tracks price changes over time.

The project is structured as a command-line application using `typer`, with a `FastAPI` backend and a simple web UI for managing and monitoring the scraper.

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

## Building and Running

### Setup

1.  Install the project dependencies:
    ```bash
    pip install -e .
    ```
2.  Create a `.env` file based on the `.env.example` file and customize the settings as needed.

### Running the Scraper

The main entry point for the application is the `vinted-scraper` command. You can use it to scrape Vinted listings with various options.

**Example:**

```bash
vinted-scraper scrape --search-text "ps5" --max-pages 10
```

This command will scrape the first 10 pages of Vinted listings for the search term "ps5".

For a full list of available options, run:

```bash
vinted-scraper scrape --help
```

### Running the Web UI

To use the web dashboard, start the FastAPI server:

```bash
uvicorn app.api.main:app --reload
```

Then, open your browser and navigate to `http://localhost:8000`.

## Development Conventions

*   **Asynchronous:** The project uses `asyncio` for all I/O-bound operations, making it highly efficient.
*   **Configuration:** The application is configured through environment variables, which are loaded into a `Settings` dataclass.
*   **Database:** The project uses `SQLAlchemy` as an ORM for database interactions, and it supports both PostgreSQL and SQLite. The database schema is defined in `app/db/models.py`.
*   **Command-line Interface:** The project uses `typer` to create a user-friendly command-line interface.
*   **Dependencies:** Project dependencies are managed using `pip` and are listed in the `pyproject.toml` file.
*   **API:** The API is built with `FastAPI` and uses `Pydantic` for data validation.

## Frontend Development

### Schema-Driven Approach (tRPC + Zod)

The frontend will be developed using a schema-driven approach with `tRPC` and `Zod`. This provides end-to-end type safety between the backend and frontend, ensuring that the API requests and responses are always in sync.

*   **`Zod`** will be used to define the validation schemas for the API data.
*   **`tRPC`** will be used to create a type-safe API layer, allowing the frontend to call backend procedures as if they were local functions.

This approach eliminates the need for manual API documentation and reduces the risk of runtime errors due to mismatched types.