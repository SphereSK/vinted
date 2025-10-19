from __future__ import annotations
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

def _as_bool(v: str | None, default: bool) -> bool:
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "y")

@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./vinted.db")
    schema: str = os.getenv("SCHEMA", "vinted")

    vinted_base_url: str = os.getenv("VINTED_BASE_URL", "https://www.vinted.sk/catalog")
    vinted_locales: list[str] = field(default_factory=lambda: os.getenv("VINTED_LOCALES", "sk").split(","))

    request_delay: float = float(os.getenv("REQUEST_DELAY", "0.5"))
    max_pages: int = int(os.getenv("MAX_PAGES", "5"))
    per_page: int = int(os.getenv("PER_PAGE", "24"))
    fetch_details: bool = _as_bool(os.getenv("FETCH_DETAILS"), True)

settings = Settings()
