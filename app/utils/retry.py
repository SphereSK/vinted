import asyncio
import time
from functools import wraps

def retry_with_backoff(retries=3, initial_delay=1, backoff_factor=2):
    """
    A decorator for retrying a function with exponential backoff.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            delay = initial_delay
            for i in range(retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if i == retries - 1:
                        raise
                    print(f"  ! Retrying {func.__name__} in {delay}s... ({e})")
                    await asyncio.sleep(delay)
                    delay *= backoff_factor
        return wrapper
    return decorator
