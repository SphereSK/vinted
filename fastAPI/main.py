"""FastAPI application entrypoint."""
from __future__ import annotations

import os
from typing import Any, Callable

from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastAPI.routers import configs, cron, listings, stats, taxonomy

# Ensure environment variables from the project-level .env are available.
load_dotenv(find_dotenv())

# Optional hooks for deploying a custom OpenAPI/Docs configuration.
_host = os.getenv("FASTAPI_HOST", "0.0.0.0")
_port_str = os.getenv("FASTAPI_PORT", "8933")
_openapi_url = os.getenv("FASTAPI_OPENAPI_URL")
_docs_url = os.getenv("FASTAPI_DOCS_URL")
_redoc_url = os.getenv("FASTAPI_REDOC_URL")
_cors_origins = os.getenv("FASTAPI_CORS_ORIGINS", "http://localhost:8934")


def _get_port() -> int:
    try:
        return int(_port_str)
    except ValueError as exc:  # pragma: no cover - invalid env input
        raise ValueError(f"FASTAPI_PORT must be an integer (got {_port_str!r})") from exc


def create_app() -> FastAPI:
    """Instantiate the FastAPI application."""
    app = FastAPI(
        title="Vinted Scraper API",
        description="API surface for the Vinted scraping and scheduling platform.",
        version="0.1.0",
    )

    # Allow local development until tighter policies are defined.
    origins = [origin.strip() for origin in _cors_origins.split(",") if origin.strip()]
    allow_all_origins = any(origin in {"*", "*:*"} for origin in origins)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if allow_all_origins else origins,
        allow_credentials=not allow_all_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Override docs/OpenAPI URLs when provided.
    if _openapi_url is not None:
        app.openapi_url = _openapi_url or None
    if _docs_url is not None:
        app.docs_url = _docs_url or None
    if _redoc_url is not None:
        app.redoc_url = _redoc_url or None

    # Register routers
    app.include_router(stats.router)
    app.include_router(listings.router)
    app.include_router(configs.router)
    app.include_router(taxonomy.router)
    app.include_router(cron.router)

    @app.get("/")
    async def root() -> dict[str, str]:  # pragma: no cover - simple health endpoint
        return {"status": "ok"}

    return app


app = create_app()


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    import uvicorn

    uvicorn.run("fastAPI.main:app", host=_host, port=_get_port(), reload=True)
