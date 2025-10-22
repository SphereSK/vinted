"""Common FastAPI dependencies shared across routers."""
from __future__ import annotations

import secrets
from collections.abc import AsyncIterator

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import Session, init_db

API_KEY_HEADER_NAME = settings.fastapi_api_key_header or "X-API-Key"
_api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    """Provide a database session bound to the shared async engine."""
    await init_db()
    async with Session() as session:
        yield session


async def require_api_key(api_key: str | None = Security(_api_key_header)) -> None:
    """Protect endpoints with a static API key when configured."""
    configured = settings.fastapi_api_key
    if not configured:
        return

    if not api_key or not secrets.compare_digest(api_key, configured):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
