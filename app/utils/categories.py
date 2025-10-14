"""
Category discovery and listing for Vinted catalogs.
"""
import asyncio
from vinted_api_kit import VintedApi


# Common category IDs for reference (Slovakia marketplace)
COMMON_CATEGORIES = {
    # Electronics & Gaming
    2994: "Electronics",
    3026: "Video Games",
    1953: "Computers",

    # Fashion
    16: "Women's Clothing",
    18: "Men's Clothing",
    12: "Kids & Baby",

    # Home & Lifestyle
    1243: "Home",
    5: "Entertainment",
}

# Video game platform IDs (used with video_game_platform_ids parameter)
VIDEO_GAME_PLATFORMS = {
    1281: "PlayStation 5",
    1280: "PlayStation 4",
    1279: "PlayStation 3",
    1278: "PlayStation 2",
    1277: "PlayStation 1",
    1286: "PlayStation Portable (PSP)",
    1287: "PlayStation Vita",
    1282: "Xbox Series X/S",
    1283: "Xbox One",
    1284: "Xbox 360",
    1285: "Xbox",
    1288: "Nintendo Switch",
    1289: "Nintendo Wii U",
    1290: "Nintendo Wii",
    1291: "Nintendo DS",
    1292: "Nintendo 3DS",
    1293: "Nintendo GameCube",
    1294: "Nintendo 64",
    1295: "Game Boy",
    1296: "Sega",
    1297: "PC Gaming",
}


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
