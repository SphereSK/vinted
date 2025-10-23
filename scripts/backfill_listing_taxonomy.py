"""Backfill listings with taxonomy option identifiers."""
from __future__ import annotations

import asyncio

from sqlalchemy import select, update, func

from app.db.models import Listing, SourceOption, ConditionOption
from app.db.session import init_db, Session
from app.utils.conditions import normalize_condition


async def backfill_listing_taxonomy() -> None:
    await init_db()

    async with Session() as session:
        async with session.begin():
            await _backfill_sources(session)
            await _backfill_conditions(session)


async def _backfill_sources(session) -> None:
    source_rows = await session.execute(select(SourceOption.id, SourceOption.code))
    source_records = source_rows.all()
    source_map = {row.code.lower(): row.id for row in source_records}
    source_id_to_code = {row.id: row.code for row in source_records}
    default_source_id = source_map.get("vinted")

    if default_source_id is not None:
        await session.execute(
            update(Listing)
            .where(func.coalesce(func.length(func.trim(Listing.source)), 0) == 0)
            .values(
                source=source_id_to_code.get(default_source_id, "vinted"),
                source_option_id=default_source_id,
            )
        )

    for code, source_id in source_map.items():
        await session.execute(
            update(Listing)
            .where(func.lower(func.trim(Listing.source)) == code)
            .values(source=source_id_to_code.get(source_id, code), source_option_id=source_id)
        )


async def _backfill_conditions(session) -> None:
    condition_rows = await session.execute(
        select(ConditionOption.id, ConditionOption.code, ConditionOption.label)
    )
    condition_records = condition_rows.all()
    condition_code_map = {row.code.lower(): row.id for row in condition_records}
    condition_label_map = {row.label.lower(): row.id for row in condition_records}
    condition_id_to_code = {row.id: row.code for row in condition_records}

    listings = await session.execute(
        select(Listing.id, Listing.condition)
    )

    for listing_id, condition in listings.all():
        condition_id, condition_code, condition_label = normalize_condition(condition)
        resolved_id = condition_id or (
            condition_code_map.get((condition_code or "").lower())
        ) or (
            condition_label_map.get((condition_label or "").strip().lower())
        )
        if resolved_id is not None:
            await session.execute(
                update(Listing)
                .where(Listing.id == listing_id)
                .values(
                    condition=condition_id_to_code.get(resolved_id, condition_code),
                    condition_option_id=resolved_id,
                )
            )


def main() -> None:
    asyncio.run(backfill_listing_taxonomy())


if __name__ == "__main__":
    main()
