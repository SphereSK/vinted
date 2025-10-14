# Vinted Scraper

## Project Overview

This project is a Python-based asynchronous web scraper for the Vinted marketplace. It is designed to collect data on product listings and store it in a PostgreSQL or SQLite database. The scraper is highly customizable, allowing users to specify search queries, categories, and other parameters. It also tracks price changes over time.

The project is structured as a command-line application using `typer`. The core scraping logic is built on top of the `vinted-api-kit` library, and it uses `SQLAlchemy` for database interactions.

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

## Development Conventions

*   **Asynchronous:** The project uses `asyncio` for all I/O-bound operations, making it highly efficient.
*   **Configuration:** The application is configured through environment variables, which are loaded into a `Settings` dataclass.
*   **Database:** The project uses `SQLAlchemy` as an ORM for database interactions, and it supports both PostgreSQL and SQLite. The database schema is defined in `app/db/models.py`.
*   **Command-line Interface:** The project uses `typer` to create a user-friendly command-line interface.
*   **Dependencies:** Project dependencies are managed using `pip` and are listed in the `pyproject.toml` file.
