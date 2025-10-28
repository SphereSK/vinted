"""
Verify status of tracked listings by checking their detail pages.

This module handles proactive checking of items we're already tracking
to determine if they've been sold, removed, or are still available.
"""
import asyncio
import time
import random
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy import select, update
from bs4 import BeautifulSoup
import requests

from app.db.models import Listing
from app.db.session import Session, init_db
from app.utils.logging import get_logger

logger = get_logger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


async def check_item_status(url: str) -> Optional[dict]:
    """
    Check if an item is still available by fetching its detail page.

    Returns:
        dict with keys: is_visible, is_active, is_sold
        None if check failed
    """
    try:
        response = await asyncio.to_thread(
            requests.get,
            url,
            headers=HEADERS,
            timeout=10
        )

        # Item removed/not found
        if response.status_code == 404:
            return {
                "is_visible": False,
                "is_active": False,
                "is_sold": False,  # Unknown - could be removed or sold
            }

        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Check for sold indicator
        # Slovak: "Predané", Polish: "Sprzedane", Czech: "Prodáno", English: "Sold"
        sold_keywords = ["Predané", "Sprzedane", "Prodáno", "Sold"]
        is_sold = any(soup.find(string=keyword) for keyword in sold_keywords)

        if is_sold:
            return {
                "is_visible": False,
                "is_active": False,
                "is_sold": True,
            }
        else:
            # Item still available for sale
            return {
                "is_visible": True,
                "is_active": True,
                "is_sold": False,
            }

    except requests.exceptions.Timeout:
        logger.warning(f"Timeout checking {url}")
        return None
    except Exception as e:
        logger.error(f"Error checking {url}: {e}")
        return None


async def verify_tracked_items(
    batch_size: int = 100,
    hours_since_last_seen: int = 24,
    delay: float = 2.0,
    check_all: bool = False,
    logger = None,
):
    """
    Verify status of items we're tracking that haven't been seen recently.

    Args:
        batch_size: Number of items to check
        hours_since_last_seen: Check items not seen in this many hours
        delay: Delay between requests (seconds)
        check_all: If True, check all items (active and inactive). If False, only check active items.
    """
    if not logger:
        logger = get_logger(__name__)

    await init_db()

    async with Session() as session:
        # Find items to verify (active but not seen recently)
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_since_last_seen)

        query = select(Listing).where(Listing.last_seen_at < cutoff_time)

        # Optionally filter to only active items
        if not check_all:
            query = query.where(Listing.is_active == True)

        query = (
            query
            .order_by(Listing.last_seen_at.asc())  # Oldest first
            .limit(batch_size)
        )

        result = await session.execute(query)
        items = result.scalars().all()

        if not items:
            scope = "all items" if check_all else "active items"
            logger.info(f"No items need verification ({scope} seen within {hours_since_last_seen} hours)")
            return

        total = len(items)
        scope = "all items" if check_all else "active items"
        logger.info(f"Verifying status of {total} {scope} not seen in {hours_since_last_seen}+ hours...")

        start_time = time.time()
        stats = {
            "still_available": 0,
            "sold": 0,
            "removed": 0,
            "errors": 0,
        }

        for idx, item in enumerate(items, 1):
            try:
                # Calculate ETA
                if idx > 1:
                    elapsed = time.time() - start_time
                    avg_time = elapsed / (idx - 1)
                    remaining = total - idx + 1
                    eta_seconds = avg_time * remaining
                    eta_str = f"{int(eta_seconds // 60)}m {int(eta_seconds % 60)}s"
                    logger.info(f"[{idx}/{total}] Checking {item.title[:50]}... (~{eta_str} remaining)")
                else:
                    logger.info(f"[{idx}/{total}] Checking {item.title[:50]}...")

                # Check status
                status = await check_item_status(item.url)

                if status is None:
                    stats["errors"] += 1
                    logger.warning(f"  ⚠️  Failed to check status")
                    continue

                # Update database
                stmt = (
                    update(Listing)
                    .where(Listing.id == item.id)
                    .values(**status)
                )
                await session.execute(stmt)
                await session.commit()

                # Log result
                if status["is_sold"]:
                    stats["sold"] += 1
                    logger.info(f"  🔴 SOLD")
                elif not status["is_visible"]:
                    stats["removed"] += 1
                    logger.info(f"  🟡 REMOVED/UNAVAILABLE")
                else:
                    stats["still_available"] += 1
                    logger.info(f"  🟢 Still available")

                # Rate limiting
                await asyncio.sleep(delay + random.uniform(0, 0.5))

            except Exception as e:
                stats["errors"] += 1
                logger.error(f"  ❌ Error: {e}")
                await session.rollback()
                continue

        # Summary
        total_time = time.time() - start_time
        logger.info("")
        logger.info("=" * 60)
        logger.info("Verification Complete!")
        logger.info(f"Time: {int(total_time // 60)}m {int(total_time % 60)}s")
        logger.info(f"Checked: {total} items")
        logger.info(f"  🟢 Still available: {stats['still_available']}")
        logger.info(f"  🔴 Sold: {stats['sold']}")
        logger.info(f"  🟡 Removed: {stats['removed']}")
        logger.info(f"  ❌ Errors: {stats['errors']}")
        logger.info("=" * 60)
