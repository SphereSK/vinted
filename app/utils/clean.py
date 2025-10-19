import re

def standardize_brand(brand: str) -> str:
    """
    Standardizes a brand name.
    """
    if not brand:
        return None

    brand = brand.lower()
    if "sony" in brand or "playstation" in brand:
        return "Sony"
    if "microsoft" in brand or "xbox" in brand:
        return "Microsoft"
    if "nintendo" in brand:
        return "Nintendo"
    return brand.title()
