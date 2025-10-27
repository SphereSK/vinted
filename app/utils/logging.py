import logging
import sys
import os

# Configure root logger based on environment variable
log_level_str = os.getenv("VINTED_SCRAPER_LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)

def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.
    The logging level is determined by the VINTED_SCRAPER_LOG_LEVEL environment variable,
    defaulting to INFO if not set.
    """
    return logging.getLogger(name)

