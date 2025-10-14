from __future__ import annotations
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from .base import Base
from ..config import settings

connect_args = {}
if settings.database_url.startswith("postgresql+asyncpg://"):
    # PgBouncer-friendly (avoid unnamed portal errors)
    connect_args["statement_cache_size"] = 0

engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    pool_pre_ping=True,
    connect_args=connect_args,
)

Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        if settings.database_url.startswith("postgresql"):
            await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{settings.schema}";'))
        await conn.run_sync(Base.metadata.create_all)
