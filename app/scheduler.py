import asyncio
import os
import re
import shlex
from pathlib import Path
import sys
import requests
from typing import Optional, Sequence
from urllib.parse import urlparse

from crontab import CronTab
from sqlalchemy import select

from app.db.models import ScrapeConfig
from app.db.session import Session, init_db

PROJECT_ROOT = Path(os.getenv("SCRAPER_WORKDIR", Path(__file__).resolve().parents[1]))
SCRAPER_COMMAND = os.getenv("SCRAPER_COMMAND")
if not SCRAPER_COMMAND:
    python_executable = os.getenv("SCRAPER_PYTHON", sys.executable)
    SCRAPER_COMMAND = f"{python_executable} -m app.cli scrape"
DEFAULT_USE_PROXY = os.getenv("SCRAPER_USE_PROXY", "false").lower() in {"1", "true", "yes"}
CRON_COMMENT_PREFIX = os.getenv("SCRAPER_CRON_COMMENT", "vinted-scraper")
MAX_EXTRA_ARG_LENGTH = int(os.getenv("SCRAPER_EXTRA_ARG_MAX_LENGTH", "128"))
SAFE_EXTRA_ARG_PATTERN = re.compile(r"^[A-Za-z0-9._:@%+=/,-[ ]&?]+$")
VALID_ORDERS = {"newest_first", "price_low_to_high", "price_high_to_low"}
VALID_DETAIL_STRATEGIES = {"browser", "http"}
LOCALE_PATTERN = re.compile(r"^[A-Za-z0-9_-]{2,10}$")
HEALTHCHECK_TIMEOUT = int(os.getenv("SCRAPER_HEALTHCHECK_TIMEOUT", "10"))
HEALTHCHECK_RETRIES = int(os.getenv("SCRAPER_HEALTHCHECK_RETRIES", "3"))
HEALTHCHECK_START_SUFFIX = os.getenv("SCRAPER_HEALTHCHECK_START_SUFFIX", "/start")
HEALTHCHECK_FAIL_SUFFIX = os.getenv("SCRAPER_HEALTHCHECK_FAIL_SUFFIX", "/fail")
LOG_FILE = PROJECT_ROOT / "logs" / "cron.log"

_fastapi_host = os.getenv("FASTAPI_HOST", "localhost")
_fastapi_port = os.getenv("FASTAPI_PORT", "8000")
FASTAPI_BASE_URL = os.getenv("FASTAPI_BASE_URL", f"http://{_fastapi_host}:{_fastapi_port}")
FASTAPI_API_KEY = os.getenv("FASTAPI_API_KEY")
FASTAPI_API_KEY_HEADER = os.getenv("FASTAPI_API_KEY_HEADER", "X-API-Key")


def _quote(value: object) -> str:
    return shlex.quote(str(value))


def load_listings_to_cache():
    try:
        requests.post(f"{FASTAPI_BASE_URL}/api/listings/load")
    except requests.exceptions.RequestException as e:
        print(f"Could not load listings to cache: {e}")

def validate_cron_expression(expression: str) -> str:
    """Validate a standard 5-field cron expression."""
    expr = expression.strip()
    if not expr:
        raise ValueError("Cron schedule cannot be empty")

    cron = CronTab()
    job = cron.new(command="true")
    try:
        job.setall(expr)
    except ValueError as exc:
        raise ValueError(f"Invalid cron expression '{expr}': {exc}") from exc

    return expr


def sanitize_extra_argument(arg: str) -> str:
    """Ensure additional CLI arguments are safe to interpolate."""
    if not isinstance(arg, str):
        raise ValueError("Extra arguments must be strings")
    value = arg.strip()
    if not value:
        raise ValueError("Extra arguments cannot be empty")
    if len(value) > MAX_EXTRA_ARG_LENGTH:
        raise ValueError(
            f"Extra argument '{value}' exceeds max length {MAX_EXTRA_ARG_LENGTH}"
        )
    if not SAFE_EXTRA_ARG_PATTERN.fullmatch(value):
        raise ValueError(
            "Extra arguments may only contain alphanumerics and - . _ : @ % + = / , [ ] & ?"
        )
    return value


def sanitize_extra_arguments(args: Optional[Sequence[str]]) -> list[str]:
    """Validate each extra argument token."""
    if not args:
        return []
    if isinstance(args, str):
        raise ValueError("Extra arguments must be provided as an array of strings")
    return [sanitize_extra_argument(arg) for arg in list(args)]


def sanitize_locales(locales: Optional[Sequence[str]]) -> list[str]:
    """Validate locale values provided for scraping."""
    if not locales:
        return []
    if isinstance(locales, str):
        raise ValueError("Locales must be provided as an array of strings")
    cleaned: list[str] = []
    for locale in locales:
        if not isinstance(locale, str):
            raise ValueError("Locales must be strings")
        value = locale.strip()
        if not value:
            raise ValueError("Locale values cannot be empty")
        if not LOCALE_PATTERN.fullmatch(value):
            raise ValueError(f"Invalid locale: {value}")
        cleaned.append(value)
    return cleaned


def validate_order(order: Optional[str]) -> Optional[str]:
    """Ensure order option matches supported CLI values."""
    if order is None:
        return None
    value = order.strip()
    if not value:
        raise ValueError("Order cannot be empty")
    if value not in VALID_ORDERS:
        allowed = ", ".join(sorted(VALID_ORDERS))
        raise ValueError(f"Order '{value}' is invalid; allowed values: {allowed}")
    return value


def validate_details_strategy(strategy: Optional[str]) -> Optional[str]:
    """Validate details fetching strategy."""
    if strategy is None:
        return None
    value = strategy.strip().lower()
    if not value:
        raise ValueError("Details strategy cannot be empty")
    if value not in VALID_DETAIL_STRATEGIES:
        allowed = ", ".join(sorted(VALID_DETAIL_STRATEGIES))
        raise ValueError(f"Details strategy '{value}' is invalid; allowed values: {allowed}")
    return value


def validate_base_url(url: Optional[str]) -> Optional[str]:
    """Ensure base URL is a valid HTTP(S) URL."""
    if url is None:
        return None
    value = url.strip()
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Base URL must include scheme (http/https) and host")
    return value


def validate_positive_int(value: Optional[int], field: str, minimum: int = 0) -> Optional[int]:
    """Ensure integer configuration values are non-negative."""
    if value is None:
        return None
    if value < minimum:
        raise ValueError(f"{field} must be >= {minimum}")
    return value


def build_scrape_command(
    *,
    search_text: str,
    max_pages: int,
    per_page: int,
    delay: float,
    categories: Optional[Sequence[int]] = None,
    platform_ids: Optional[Sequence[int]] = None,
    fetch_details: bool = False,
    details_for_new_only: bool = False,
    use_proxy: Optional[bool] = None,
    extra_filters: Optional[Sequence[str]] = None,
    order: Optional[str] = None,
    locales: Optional[Sequence[str]] = None,
    error_wait_minutes: Optional[int] = None,
    max_retries: Optional[int] = None,
    base_url: Optional[str] = None,
    details_strategy: Optional[str] = None,
    details_concurrency: Optional[int] = None,
    extra_args: Optional[Sequence[str]] = None,
    workdir: Optional[Path | str] = None,
    healthcheck_ping_url: Optional[str] = None,
    config_id: Optional[int] = None,
) -> str:
    """
    Construct the CLI command used to run a scrape job.

    Parameters mirror the ScrapeConfig attributes and allow optional overrides.
    """

    tokens = shlex.split(SCRAPER_COMMAND)
    if not tokens:
        raise ValueError("SCRAPER_COMMAND must specify at least one token")

    sanitized_order = validate_order(order)
    sanitized_extras = sanitize_extra_arguments(extra_filters)
    sanitized_locales = sanitize_locales(locales)
    sanitized_error_wait = validate_positive_int(error_wait_minutes, "error_wait_minutes", minimum=0)
    sanitized_max_retries = validate_positive_int(max_retries, "max_retries", minimum=0)
    sanitized_base_url = validate_base_url(base_url)
    sanitized_details_strategy = validate_details_strategy(details_strategy)
    sanitized_details_concurrency = validate_positive_int(
        details_concurrency, "details_concurrency", minimum=1
    )

    tokens.extend(["--search-text", search_text])
    tokens.extend(["--max-pages", str(max_pages)])
    tokens.extend(["--per-page", str(per_page)])
    tokens.extend(["--delay", str(delay)])

    for cat_id in categories or []:
        tokens.extend(["-c", str(cat_id)])

    for plat_id in platform_ids or []:
        tokens.extend(["-p", str(plat_id)])

    if fetch_details:
        tokens.append("--fetch-details")

    if details_for_new_only:
        tokens.append("--details-for-new-only")

    if sanitized_order:
        tokens.extend(["--order", sanitized_order])

    for extra_filter in sanitized_extras:
        tokens.extend(["-e", extra_filter])

    for locale in sanitized_locales:
        tokens.extend(["--locale", locale])

    resolved_use_proxy = DEFAULT_USE_PROXY if use_proxy is None else use_proxy
    if not resolved_use_proxy:
        tokens.append("--no-proxy")

    if sanitized_error_wait is not None:
        tokens.extend(["--error-wait", str(sanitized_error_wait)])

    if sanitized_max_retries is not None:
        tokens.extend(["--max-retries", str(sanitized_max_retries)])

    if sanitized_base_url:
        tokens.extend(["--base-url", sanitized_base_url])

    if sanitized_details_strategy:
        tokens.extend(["--details-strategy", sanitized_details_strategy])

    if sanitized_details_concurrency is not None:
        tokens.extend(["--details-concurrency", str(sanitized_details_concurrency)])

    safe_extra_args = sanitize_extra_arguments(extra_args)
    for arg in safe_extra_args:
        tokens.extend(shlex.split(arg))

    if config_id is not None:
        tokens.extend(["--config-id", str(config_id)])

    command = " ".join(_quote(token) for token in tokens)
    cwd = Path(workdir) if workdir else PROJECT_ROOT
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "cron.log"

    # Redirect output to log file
    command_with_logging = f"{command} >> {log_file} 2>&1"

    if config_id:
        # Always ping internal health check endpoint
        internal_health_url = f"{FASTAPI_BASE_URL}/api/cron/health/{config_id}"
        curl_cmd_success_internal = f"curl -fsS -m {HEALTHCHECK_TIMEOUT} --retry {HEALTHCHECK_RETRIES} -X POST -H 'Content-Type: application/json' -H '{FASTAPI_API_KEY_HEADER}: {FASTAPI_API_KEY}' -d '{{\"status\":\"ok\"}}' {_quote(internal_health_url)}"
        curl_cmd_fail_internal = f"curl -fsS -m {HEALTHCHECK_TIMEOUT} --retry {HEALTHCHECK_RETRIES} -X POST -H 'Content-Type: application/json' -H '{FASTAPI_API_KEY_HEADER}: {FASTAPI_API_KEY}' -d '{{\"status\":\"fail\"}}' {_quote(internal_health_url)}"

        success_commands = [curl_cmd_success_internal]
        fail_commands = [curl_cmd_fail_internal]

        # If healthchecks.io URL is provided, add it to the commands
        if healthcheck_ping_url:
            sanitized_ping = validate_base_url(healthcheck_ping_url)
            base_ping = sanitized_ping.rstrip("/")
            success_url_external = base_ping
            fail_url_external = f"{base_ping}{HEALTHCHECK_FAIL_SUFFIX}"
            curl_cmd_success_external = f"curl -fsS -m {HEALTHCHECK_TIMEOUT} --retry {HEALTHCHECK_RETRIES} {_quote(success_url_external)}"
            curl_cmd_fail_external = f"curl -fsS -m {HEALTHCHECK_TIMEOUT} --retry {HEALTHCHECK_RETRIES} {_quote(fail_url_external)}"
            success_commands.append(curl_cmd_success_external)
            fail_commands.append(curl_cmd_fail_external)
        
        success_command_str = " && ".join(f"({cmd} >/dev/null 2>&1)" for cmd in success_commands)
        fail_command_str = " && ".join(f"({cmd} >/dev/null 2>&1)" for cmd in fail_commands)

        wrapped = f"({command_with_logging}; status=$?; if [ $status -eq 0 ]; then {success_command_str}; else {fail_command_str}; fi; exit $status)"
        return f"cd {_quote(cwd)} && {wrapped}"

    return f"cd {_quote(cwd)} && {command_with_logging}"


def get_user_crontab() -> CronTab:
    """Get the current user's crontab."""
    return CronTab(user=True)


async def sync_crontab() -> None:
    """
    Sync scrape configurations with system crontab.
    This function should be called whenever configs are created/updated/deleted.
    """
    await init_db()
    cron = get_user_crontab()

    # Remove all existing vinted-scraper jobs
    await asyncio.to_thread(_purge_vinted_jobs, cron)

    # Get all active configs with cron schedules
    async with Session() as session:
        result = await session.execute(
            select(ScrapeConfig).where(
                ScrapeConfig.is_active.is_(True),
                ScrapeConfig.cron_schedule.isnot(None),
            )
        )
        configs = result.scalars().all()

        # Add new jobs using wrapper script to avoid line length limits
        wrapper_script = PROJECT_ROOT / "run-scraper-cron.sh"
        if not wrapper_script.exists():
            raise FileNotFoundError(f"Wrapper script not found: {wrapper_script}")

        for config in configs:
            if not config.cron_schedule:
                continue

            # Use wrapper script with config ID - much shorter command
            command = f"{wrapper_script} {config.id}"

            job = await asyncio.to_thread(cron.new, command=command, comment=f"{CRON_COMMENT_PREFIX}:{config.id}")
            await asyncio.to_thread(job.setall, validate_cron_expression(config.cron_schedule))

    # Write to system
    await asyncio.to_thread(cron.write)
    await asyncio.to_thread(load_listings_to_cache)


async def list_scheduled_jobs() -> list[dict[str, object]]:
    """List all scheduled vinted-scraper jobs."""
    cron = get_user_crontab()
    jobs: list[dict[str, object]] = []

    for job in cron:
        comment = job.comment or ""
        if not comment.startswith(CRON_COMMENT_PREFIX):
            continue

        config_id = None
        if ":" in comment:
            _, _, suffix = comment.partition(":")
            if suffix.isdigit():
                config_id = int(suffix)

        jobs.append(
            {
                "schedule": str(job.slices),
                "command": job.command,
                "enabled": job.is_enabled(),
                "comment": comment,
                "config_id": config_id,
            }
        )

    return jobs


async def remove_all_jobs() -> int:
    """Remove all vinted-scraper cron jobs."""
    cron = get_user_crontab()
    count = await asyncio.to_thread(_purge_vinted_jobs, cron)
    await asyncio.to_thread(cron.write)
    return count


def _purge_vinted_jobs(cron: CronTab) -> int:
    """Remove jobs with the configured comment prefix."""
    removed = 0
    for job in list(cron):
        comment = job.comment or ""
        if comment.startswith(CRON_COMMENT_PREFIX):
            cron.remove(job)
            removed += 1
    return removed


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "sync":
            asyncio.run(sync_crontab())
        elif sys.argv[1] == "list":
            jobs = asyncio.run(list_scheduled_jobs())
            if jobs:
                print("\n📋 Scheduled Jobs:")
                for job in jobs:
                    print(f"  Schedule: {job['schedule']}")
                    print(f"  Command: {job['command']}")
                    print(f"  Enabled: {job['enabled']}\n")
            else:
                print("No scheduled jobs found.")
        elif sys.argv[1] == "clear":
            count = asyncio.run(remove_all_jobs())
            print(f"Removed {count} jobs.")
    else:
        print("Usage: python -m app.scheduler [sync|list|clear]")
