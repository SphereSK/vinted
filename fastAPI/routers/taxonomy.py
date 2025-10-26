"""Taxonomy endpoints (categories, platforms, conditions, sources)."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends

from app.api.schemas import CategoryResponse, ConditionResponse, SourceResponse, PlatformResponse
from app.db.models import (
    CategoryOption,
    PlatformOption,
    ConditionOption,
    SourceOption,
)
from fastAPI.dependencies import get_db, require_api_key

router = APIRouter(
    prefix="/api",
    tags=["taxonomy"],
    dependencies=[Depends(require_api_key)],
)


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)) -> list[CategoryResponse]:
    """Return available categories from the master data table."""
    records = (
        await db.execute(
        select(CategoryOption).order_by(CategoryOption.name.asc())
        )
    ).scalars().all()
    return [CategoryResponse(id=row.id, name=row.name, color=row.color) for row in records]


@router.get("/platforms", response_model=list[PlatformResponse])
async def list_platforms(db: AsyncSession = Depends(get_db)) -> list[PlatformResponse]:
    """Return available platforms from the master data table."""
    records = (
        await db.execute(
        select(PlatformOption).order_by(PlatformOption.name.asc())
        )
    ).scalars().all()
    return [PlatformResponse(id=row.id, name=row.name, color=row.color) for row in records]


@router.get("/conditions", response_model=list[ConditionResponse])
async def list_conditions(
    db: AsyncSession = Depends(get_db),
) -> list[ConditionResponse]:
    """Return canonical condition options."""
    records = (
        await db.execute(
            select(ConditionOption).order_by(ConditionOption.label.asc())
        )
    ).scalars().all()
    return [ConditionResponse(id=row.id, code=row.code, label=row.label, color=row.color) for row in records]


@router.get("/sources", response_model=list[SourceResponse])
async def list_sources(
    db: AsyncSession = Depends(get_db),
) -> list[SourceResponse]:
    """Return canonical source options."""
    records = (
        await db.execute(
            select(SourceOption).order_by(SourceOption.label.asc())
        )
    ).scalars().all()
    return [SourceResponse(id=row.id, code=row.code, label=row.label, color=row.color) for row in records]