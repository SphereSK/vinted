"""Taxonomy endpoints (categories, platforms)."""
from fastapi import APIRouter, Depends

from app.api.schemas import CategoryResponse
from app.utils.categories import list_common_categories, list_video_game_platforms
from fastAPI.dependencies import require_api_key

router = APIRouter(
    prefix="/api",
    tags=["taxonomy"],
    dependencies=[Depends(require_api_key)],
)


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories() -> list[CategoryResponse]:
    """Return available categories."""
    categories = list_common_categories()
    return [
        CategoryResponse(id=int(cat_id), name=name)
        for cat_id, name in categories.items()
    ]


@router.get("/platforms", response_model=list[CategoryResponse])
async def list_platforms() -> list[CategoryResponse]:
    """Return available platforms."""
    platforms = list_video_game_platforms()
    return [
        CategoryResponse(id=int(plat_id), name=name)
        for plat_id, name in platforms.items()
    ]
