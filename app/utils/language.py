import logging
import sys
from langdetect import detect, LangDetectException

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
    print(f"[DEBUG] detect_language - Input text (first 100 chars): {text[:100]}... Min length: {min_length}")
    if not text or len(text.strip()) < min_length:
        print(f"[DEBUG] detect_language - Text too short or empty. Length: {len(text.strip()) if text else 0}")
        return None

    try:
        # langdetect returns ISO 639-1 codes (2-letter)
        lang = detect(text)
        print(f"[DEBUG] detect_language - Detected: {lang}")
        return lang
    except LangDetectException as e:
        print(f"[DEBUG] detect_language - LangDetectException for text: {text[:50]}... Error: {e}")
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
    print(f"[DEBUG] detect_language_from_keywords - Input text: {text}")
    if not text:
        print("[DEBUG] detect_language_from_keywords - Text is empty.")
        return None

    text_lower = text.lower()

    # Polish indicators (common words in Polish game listings)
    polish_keywords = ['gra', 'nowa', 'nowy', 'nowe', 'folia', 'używana', 'stan', 'edycja']
    if any(keyword in text_lower for keyword in polish_keywords):
        print("[DEBUG] detect_language_from_keywords - Detected Polish.")
        return 'pl'

    # Slovak indicators
    slovak_keywords = ['hra', 'nová', 'nový', 'nové', 'konzola', 'použitá']
    if any(keyword in text_lower for keyword in slovak_keywords):
        print("[DEBUG] detect_language_from_keywords - Detected Slovak.")
        return 'sk'

    # Czech indicators
    czech_keywords = ['perfektní', 'stavu', 'bazarový']
    if any(keyword in text_lower for keyword in czech_keywords):
        print("[DEBUG] detect_language_from_keywords - Detected Czech.")
        return 'cs'

    print("[DEBUG] detect_language_from_keywords - No keyword match.")
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
    print(f"[DEBUG] detect_language_from_item - Title: {title}")
    print(f"[DEBUG] detect_language_from_item - Description (first 100 chars): {description[:100] if description else ''}...")

    # Priority 1: If we have a description, use it for more accurate detection
    if description and len(description) > 50:
        combined_text = f"{title} {description[:300]}"
        print(f"[DEBUG] detect_language_from_item - Attempting P1 (desc+title) for: {combined_text[:100]}...")
        lang = detect_language(combined_text, min_length=30)
        if lang:
            print(f"[DEBUG] detect_language_from_item - P1 detected language: {lang}")
            return lang
        else:
            print("[DEBUG] detect_language_from_item - P1 failed to detect language.")

    # Priority 2: Try keyword-based detection on title
    print(f"[DEBUG] detect_language_from_item - Attempting P2 (keywords) for title: {title}")
    keyword_lang = detect_language_from_keywords(title)
    if keyword_lang:
        print(f"[DEBUG] detect_language_from_item - P2 detected language: {keyword_lang}")
        return keyword_lang
    else:
        print("[DEBUG] detect_language_from_item - P2 failed to detect language.")

    # Priority 3: If title is long enough, try langdetect
    if len(title) > 10:
        print(f"[DEBUG] detect_language_from_item - Attempting P3 (langdetect title) for: {title}")
        lang = detect_language(title, min_length=15)
        if lang:
            print(f"[DEBUG] detect_language_from_item - P3 detected language: {lang}")
            return lang
        else:
            print("[DEBUG] detect_language_from_item - P3 failed to detect language.")

    print(f"[DEBUG] detect_language_from_item - No reliable language detection for title: {title}, description: {description[:100] if description else ''}...")
    # Not enough information for reliable detection
    return None
