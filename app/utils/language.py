"""Language detection utilities."""
from langdetect import detect, LangDetectException
import logging

logger = logging.getLogger(__name__)


def detect_language(text: str, min_length: int = 30) -> str:
    """
    Detect language from text using langdetect.

    Args:
        text: Text to analyze (typically title + description)
        min_length: Minimum text length for reliable detection

    Returns:
        ISO 639-1 language code (e.g., 'en', 'sk', 'pl', 'cs') or None if not enough text
    """
    if not text or len(text.strip()) < min_length:
        return None

    try:
        # langdetect returns ISO 639-1 codes (2-letter)
        lang = detect(text)
        return lang
    except LangDetectException as e:
        logger.debug(f"Language detection failed for text: {text[:50]}... Error: {e}")
        return None


def detect_language_from_keywords(text: str) -> str:
    """
    Detect language using keyword patterns for short texts.
    Useful when description is not available (catalog-only scraping).

    Args:
        text: Text to analyze (typically just title)

    Returns:
        Language code or None if no clear pattern
    """
    if not text:
        return None

    text_lower = text.lower()

    # Polish indicators (common words in Polish game listings)
    polish_keywords = ['gra', 'nowa', 'nowy', 'nowe', 'folia', 'używana', 'stan', 'edycja']
    if any(keyword in text_lower for keyword in polish_keywords):
        return 'pl'

    # Slovak indicators
    slovak_keywords = ['hra', 'nová', 'nový', 'nové', 'konzola', 'použitá']
    if any(keyword in text_lower for keyword in slovak_keywords):
        return 'sk'

    # Czech indicators
    czech_keywords = ['perfektní', 'stavu', 'bazarový']
    if any(keyword in text_lower for keyword in czech_keywords):
        return 'cs'

    return None


def detect_language_from_item(title: str, description: str = None) -> str:
    """
    Detect language from item title and description.
    Returns None if detection is not reliable (not enough text).

    Priority:
    1. If description available (50+ chars) → use langdetect on title+description
    2. If title has language keywords → use keyword detection
    3. If title is long (40+ chars) → use langdetect on title
    4. Otherwise → return None (not enough data)

    Args:
        title: Item title
        description: Item description (optional, available with --fetch-details)

    Returns:
        ISO 639-1 language code or None if detection not reliable
    """
    # Priority 1: If we have a description, use it for more accurate detection
    if description and len(description) > 50:
        combined_text = f"{title} {description[:300]}"
        lang = detect_language(combined_text, min_length=30)
        if lang:
            return lang

    # Priority 2: Try keyword-based detection on title
    keyword_lang = detect_language_from_keywords(title)
    if keyword_lang:
        return keyword_lang

    # Priority 3: If title is long enough, try langdetect
    if len(title) > 40:
        lang = detect_language(title, min_length=30)
        if lang:
            return lang

    # Not enough information for reliable detection
    return None
