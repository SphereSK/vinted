"""
Category discovery and listing for Vinted catalogs.
"""
import asyncio
from vinted_api_kit import VintedApi


from app.data.taxonomy import MASTER_CATEGORIES, MASTER_PLATFORMS

COMMON_CATEGORIES = MASTER_CATEGORIES
VIDEO_GAME_PLATFORMS = MASTER_PLATFORMS


async def discover_categories(search_text: str, locale: str = "sk"):
    """
    Discover categories by performing a search and analyzing the response.
    Returns a list of suggested categories based on search results.
    """
    async with VintedApi(locale=locale) as v:
        try:
            # Perform a broad search to see what categories appear
            items = await v.search_items(
                url=f"https://www.vinted.{locale}/catalog?search_text={search_text}",
                per_page=50
            )

            if not items:
                return []

            # Extract catalog IDs from items if available
            categories_found = set()
            for item in items:
                # Try to find catalog_id in raw item data
                if hasattr(item, 'catalog_id'):
                    categories_found.add(item.catalog_id)
                elif hasattr(item, '__dict__'):
                    # Check raw attributes
                    if 'catalog_id' in item.__dict__:
                        categories_found.add(item.__dict__['catalog_id'])

            return list(categories_found)
        except Exception as e:
            print(f"Error discovering categories: {e}")
            return []


def list_common_categories():
    """List commonly used category IDs."""
    return COMMON_CATEGORIES


def list_video_game_platforms():
    """List video game platform IDs."""
    return VIDEO_GAME_PLATFORMS


def get_category_name(category_id: int) -> str:
    """Get the name of a category by its ID."""
    return COMMON_CATEGORIES.get(category_id, f"Category {category_id}")


def get_platform_name(platform_id: int) -> str:
    """Get the name of a video game platform by its ID."""
    return VIDEO_GAME_PLATFORMS.get(platform_id, f"Platform {platform_id}")


def search_categories(query: str) -> dict:
    """Search for categories matching a query string."""
    query_lower = query.lower()
    return {
        cat_id: name
        for cat_id, name in COMMON_CATEGORIES.items()
        if query_lower in name.lower()
    }


def search_platforms(query: str) -> dict:
    """Search for video game platforms matching a query string."""
    query_lower = query.lower()
    return {
        plat_id: name
        for plat_id, name in VIDEO_GAME_PLATFORMS.items()
        if query_lower in name.lower()
    }
