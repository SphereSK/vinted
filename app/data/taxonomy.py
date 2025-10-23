"""Canonical taxonomy definitions for categories, platforms, conditions, and sources."""
from __future__ import annotations

MASTER_CATEGORIES: dict[int, str] = {
    # Electronics & Gaming
    2994: "Electronics",
    3026: "Video Games",
    1953: "Computers",
    184: "Mobile Phones",
    188: "Tablets",
    3013: "Consoles",
    3055: "Accessories",
    5: "Books & Entertainment",
    1243: "Home & Living",
    1261: "Collectibles",
    # Fashion (selected common categories)
    16: "Women's Clothing",
    18: "Men's Clothing",
    12: "Kids & Baby",
    1: "Women",
    2: "Men",
    4: "Kids",
}

MASTER_PLATFORMS: dict[int, str] = {
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

MASTER_CONDITIONS: dict[int, dict[str, str]] = {
    1: {"code": "new_with_tags", "label": "New with tags"},
    2: {"code": "new", "label": "New"},
    3: {"code": "like_new", "label": "Like new"},
    4: {"code": "very_good", "label": "Very good"},
    5: {"code": "good", "label": "Good"},
    6: {"code": "satisfactory", "label": "Satisfactory"},
    7: {"code": "fair", "label": "Fair"},
    8: {"code": "poor", "label": "Poor"},
    9: {"code": "needs_repair", "label": "Needs repair"},
    10: {"code": "unknown", "label": "Unknown"},
}

MASTER_SOURCES: dict[int, dict[str, str]] = {
    1: {"code": "vinted", "label": "Vinted"},
    2: {"code": "bazos", "label": "Bazos"},
    3: {"code": "manual", "label": "Manual import"},
    4: {"code": "unknown", "label": "Unknown"},
}

CONDITION_CODE_TO_ID: dict[str, int] = {
    data["code"]: condition_id for condition_id, data in MASTER_CONDITIONS.items()
}
CONDITION_LABEL_TO_ID: dict[str, int] = {
    data["label"].lower(): condition_id for condition_id, data in MASTER_CONDITIONS.items()
}

SOURCE_CODE_TO_ID: dict[str, int] = {
    data["code"]: source_id for source_id, data in MASTER_SOURCES.items()
}
SOURCE_LABEL_TO_ID: dict[str, int] = {
    data["label"].lower(): source_id for source_id, data in MASTER_SOURCES.items()
}
