import os
import httpx
import asyncio
from app.utils.retry import retry_with_backoff
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Rate limit: 20 requests per minute = 3 seconds per request
LLM_REQUEST_DELAY = 3.0

# Define API endpoints for different providers
LLM_PROVIDER_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
LLM_PROVIDER_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

@retry_with_backoff(retries=5, initial_delay=LLM_REQUEST_DELAY, backoff_factor=2)
async def _call_llm_api(provider_url: str, api_key: str, model: str, prompt_messages: list) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url=provider_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": prompt_messages,
                "temperature": 0.2, # Keep it low for more consistent corrections
            },
            timeout=30.0 # 30 seconds timeout
        )
        response.raise_for_status() # Raise an exception for 4xx or 5xx responses
        
        response_data = response.json()
        logger.debug(f"LLM API raw response: {response_data}")
        corrected_title = response_data["choices"][0]["message"]["content"].strip()
        
        # Basic post-processing to ensure only the title is returned
        if corrected_title.startswith("Corrected title:"):
            corrected_title = corrected_title.replace("Corrected title:", "").strip()
        
        logger.debug(f"LLM API parsed corrected title: {corrected_title}")
        return corrected_title

async def correct_title_with_llm(original_title: str) -> str:
    """
    Corrects and standardizes a product title using an LLM from the configured provider.
    Requires PROVIDER, LLM_API_KEY, and LLM_MODEL environment variables to be set.
    """
    provider = os.getenv("PROVIDER")
    api_key = os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL")

    logger.debug(f"LLM Config: PROVIDER={provider}, LLM_MODEL={model}, API_KEY_SET={bool(api_key)}")

    if not provider:
        logger.warning("PROVIDER environment variable not set. Skipping LLM title correction.")
        return original_title
    if not api_key:
        logger.warning(f"LLM_API_KEY not set for provider {provider}. Skipping LLM title correction.")
        return original_title
    if not model:
        logger.warning(f"LLM_MODEL not set for provider {provider}. Skipping LLM title correction.")
        return original_title

    provider_url = None
    if provider.upper() == "OPENROUTER":
        provider_url = LLM_PROVIDER_OPENROUTER_URL
    elif provider.upper() == "GROQ":
        provider_url = LLM_PROVIDER_GROQ_URL
    else:
        logger.warning(f"Unsupported LLM provider: {provider}. Skipping LLM title correction.")
        return original_title

    prompt_messages = [
        {"role": "system", "content": "You are a helpful assistant that corrects, standardizes, and translates product titles into English. Correct typos and make titles consistent. For console games, prioritize standardizing platform names (e.g., 'PS5', 'Xbox Series X', 'Nintendo Switch'), remove unnecessary regional indicators (e.g., 'PL', 'EU'), and simplify special edition names where appropriate. Always output the corrected and standardized title in English. Examples: 'Mafia The ols country' -> 'Mafia The Old Country', 'PS4 Gra Marvel’s Spider-Man PL' -> 'PS4 Marvel's Spider-Man', 'Ghost of Yotei' -> 'Ghost of Yötei', 'Xbox One Cyberpunk 2077 Day One Edition' -> 'Xbox One Cyberpunk 2077', 'Nintendo Switch Zelda BOTW' -> 'Nintendo Switch The Legend of Zelda: Breath of the Wild', 'Syberia 3, edycja kolekcjonerska' -> 'Syberia 3 Collector's Edition', 'Battlefield 6 PS5' -> 'Battlefield 2042 PS5', 'Assassin's Creed: Syndicate PS4 and PS5' -> 'Assassin's Creed: Syndicate PS4 & PS5'. Only return the corrected title, nothing else."},
        {"role": "user", "content": f"Correct and standardize this title: {original_title}"}
    ]

    try:
        corrected_title = await _call_llm_api(provider_url, api_key, model, prompt_messages)
        await asyncio.sleep(LLM_REQUEST_DELAY) # Enforce rate limit
        return corrected_title

    except httpx.RequestError as e:
        logger.error(f"An error occurred while requesting LLM API ({provider}): {e}")
        return original_title
    except httpx.HTTPStatusError as e:
        logger.error(f"LLM API ({provider}) returned an error: {e.response.status_code} - {e.response.text}")
        return original_title
    except Exception as e:
        logger.error(f"An unexpected error occurred during LLM title correction ({provider}): {e}")
        return original_title
