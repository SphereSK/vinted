"""
Seed the taxonomy master tables with initial values.

Usage:
    python -m scripts.seed_taxonomy
"""
from __future__ import annotations

import asyncio

from sqlalchemy import insert, update, select, func

from app.data.taxonomy import (
    MASTER_CATEGORIES,
    MASTER_PLATFORMS,
    MASTER_SOURCES,
    MASTER_CONDITIONS,
)
from app.db.models import (
    CategoryOption,
    PlatformOption,
    ConditionOption,
    SourceOption,
    Listing,
)
from app.db.session import init_db, Session


async def seed_taxonomy() -> None:
    await init_db()

    async with Session() as session:
        async with session.begin():
            await _upsert_categories(session)
            await _upsert_platforms(session)
            await _upsert_conditions(session)
            await _upsert_sources(session)
            await _normalize_listing_options(session)


async def _upsert_categories(session) -> None:
    await _merge_rows(
        session,
        CategoryOption,
        [{"id": cat_id, "name": name} for cat_id, name in MASTER_CATEGORIES.items()],
    )


async def _upsert_platforms(session) -> None:
    await _merge_rows(
        session,
        PlatformOption,
        [{"id": plat_id, "name": name} for plat_id, name in MASTER_PLATFORMS.items()],
    )


async def _upsert_conditions(session) -> None:
    await _merge_rows(
        session,
        ConditionOption,
        [
            {"id": condition_id, "code": data["code"], "label": data["label"]}
            for condition_id, data in MASTER_CONDITIONS.items()
        ],
    )


async def _upsert_sources(session) -> None:
    sources = dict(MASTER_SOURCES)
    if 1 not in sources:
        sources[1] = {"code": "vinted", "label": "Vinted"}

    await _merge_rows(
        session,
        SourceOption,
        [
            {"id": source_id, "code": data["code"], "label": data["label"]}
            for source_id, data in sources.items()
        ],
    )


async def _merge_rows(session, model, rows):
    for row in rows:
        await session.merge(model(**row))


async def _normalize_listing_options(session) -> None:
    """Ensure existing listings reference canonical taxonomy IDs."""
    # Source linkage
    source_result = await session.execute(select(SourceOption.id, SourceOption.code))
    source_records = source_result.all()
    source_map = {row.code.lower(): row.id for row in source_records}
    source_id_to_code = {row.id: row.code for row in source_records}
    default_source_id = source_map.get("vinted")

    if default_source_id is not None:
        await session.execute(
            update(Listing)
            .where(func.coalesce(func.length(func.trim(Listing.source)), 0) == 0)
            .values(source=source_id_to_code.get(default_source_id, "vinted"), source_option_id=default_source_id)
        )

    for code, source_id in source_map.items():
        await session.execute(
            update(Listing)
            .where(func.lower(func.trim(Listing.source)) == code)
            .values(source=source_id_to_code.get(source_id, code), source_option_id=source_id)
        )

    # Condition linkage
    condition_result = await session.execute(
        select(ConditionOption.id, ConditionOption.code, ConditionOption.label)
    )
    condition_records = condition_result.all()
    condition_code_map = {row.code.lower(): row.id for row in condition_records}
    condition_label_map = {row.label.lower(): row.id for row in condition_records}
    condition_id_to_code = {row.id: row.code for row in condition_records}

    for code, condition_id in condition_code_map.items():
        await session.execute(
            update(Listing)
            .where(func.lower(func.trim(Listing.condition)) == code)
            .values(condition=condition_id_to_code.get(condition_id, code), condition_option_id=condition_id)
        )

    for label, condition_id in condition_label_map.items():
        await session.execute(
            update(Listing)
            .where(func.lower(func.trim(Listing.condition)) == label)
            .values(condition=condition_id_to_code.get(condition_id, label), condition_option_id=condition_id)
        )


def main() -> None:
    asyncio.run(seed_taxonomy())


if __name__ == "__main__":
    main()
