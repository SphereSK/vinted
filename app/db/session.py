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
    await _seed_master_data()


async def _seed_master_data() -> None:
    """Populate taxonomy master data tables with canonical entries."""
    from app.data.taxonomy import (
        MASTER_CATEGORIES,
        MASTER_PLATFORMS,
        MASTER_CONDITIONS,
        MASTER_SOURCES,
    )
    from app.db.models import (
        CategoryOption,
        PlatformOption,
        ConditionOption,
        SourceOption,
    )

    async with Session() as session:
        dirty = False

        for cat_id, name in MASTER_CATEGORIES.items():
            existing = await session.get(CategoryOption, cat_id)
            if existing:
                if existing.name != name:
                    existing.name = name
                    dirty = True
            else:
                session.add(CategoryOption(id=cat_id, name=name))
                dirty = True

        for platform_id, name in MASTER_PLATFORMS.items():
            existing = await session.get(PlatformOption, platform_id)
            if existing:
                if existing.name != name:
                    existing.name = name
                    dirty = True
            else:
                session.add(PlatformOption(id=platform_id, name=name))
                dirty = True

        for condition_id, data in MASTER_CONDITIONS.items():
            existing = await session.get(ConditionOption, condition_id)
            if existing:
                if existing.code != data["code"] or existing.label != data["label"]:
                    existing.code = data["code"]
                    existing.label = data["label"]
                    dirty = True
            else:
                session.add(
                    ConditionOption(id=condition_id, code=data["code"], label=data["label"])
                )
                dirty = True

        for source_id, data in MASTER_SOURCES.items():
            existing = await session.get(SourceOption, source_id)
            if existing:
                if existing.code != data["code"] or existing.label != data["label"]:
                    existing.code = data["code"]
                    existing.label = data["label"]
                    dirty = True
            else:
                session.add(
                    SourceOption(id=source_id, code=data["code"], label=data["label"])
                )
                dirty = True

        if dirty:
            await session.commit()
