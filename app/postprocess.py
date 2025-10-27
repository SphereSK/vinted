import asyncio
import time
import random
from sqlalchemy import select, update
from app.db.models import Listing
from app.db.session import Session, init_db
from app.utils.language import detect_language_from_item
from app.utils.logging import get_logger
from app.utils.title_corrector import correct_title_with_llm


async def process_language_detection(
    limit: int = None,
    source: str = None,
    logger = None,
):
    """
    Post-process existing listings to detect language.

    Fetches HTML for listings without language data and extracts language info.
    This is separate from the main scraping flow for better performance.

    Args:
        limit: Maximum number of listings to process (None = all)
        source: Filter by source (e.g., 'vinted', 'bazos')
    """
    if not logger:
        logger = get_logger(__name__)

    await init_db()

    async with Session() as session:
        # Find listings without language
        query = select(Listing).where(
            Listing.language.is_(None),
            Listing.is_active == True
        )

        if source:
            query = query.where(Listing.source == source)

        if limit:
            query = query.limit(limit)

        result = await session.execute(query)
        listings = result.scalars().all()

        if not listings:
            logger.info("No listings need language detection")
            return

        total = len(listings)
        logger.info(f"Processing {total} listing(s) for language detection...")

        processed = 0
        errors = 0
        start_time = time.time()

        for idx, listing in enumerate(listings, 1):
            try:
                # Calculate ETA
                if idx > 1:
                    elapsed = time.time() - start_time
                    avg_time = elapsed / (idx - 1)
                    remaining = total - idx + 1
                    eta_seconds = avg_time * remaining
                    eta_str = f"{int(eta_seconds // 60)}m {int(eta_seconds % 60)}s"
                    logger.info(f"[{idx}/{total}] ~{eta_str} remaining")
                else:
                    logger.info(f"[{idx}/{total}]")

                # Detect language using existing DB data
                detected_lang = await asyncio.to_thread(detect_language_from_item,
                    title=listing.title or "",
                    description=listing.description or ""
                )

                # Update listing
                if detected_lang:
                    stmt = (
                        update(Listing)
                        .where(Listing.id == listing.id)
                        .values(
                            language=detected_lang,
                        )
                    )
                    await session.execute(stmt)
                    await session.commit()

                    logger.info(f"Language: {detected_lang}")
                    processed += 1
                else:
                    logger.warning("Could not detect language")
                    errors += 1

            except Exception as e:
                logger.error(f"Error: {e}")
                errors += 1
                await session.rollback()
                continue

        elapsed = time.time() - start_time
        elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"

        logger.info("Completed in %s", elapsed_str)
        logger.info(f"Processed: {processed}")
        logger.info(f"Errors: {errors}")
        logger.info(f"Total: {total}")

async def process_title_correction(
    limit: int = None,
    delay: float = 1.5,
    source: str = None,
    logger = None,
):
    """
    Post-process existing listings to correct and standardize titles using an LLM.

    Args:
        limit: Maximum number of listings to process (None = all)
        delay: Delay between requests in seconds (default: 1.5)
        source: Filter by source (e.g., 'vinted', 'bazos')
    """
    if not logger:
        logger = get_logger(__name__)

    await init_db()

    async with Session() as session:
        # Find listings where title is the same as original_title (meaning it hasn't been corrected yet)
        # and is_active is True
        query = select(Listing).where(
            Listing.title == Listing.original_title,
            Listing.is_active == True
        )

        if source:
            query = query.where(Listing.source == source)

        if limit:
            query = query.limit(limit)

        result = await session.execute(query)
        listings = result.scalars().all()

        if not listings:
            logger.info("No listings need title correction")
            return

        total = len(listings)
        logger.info(f"Processing {total} listing(s) for title correction...")

        processed = 0
        errors = 0
        start_time = time.time()

        for idx, listing in enumerate(listings, 1):
            try:
                # Calculate ETA
                if idx > 1:
                    elapsed = time.time() - start_time
                    avg_time = elapsed / (idx - 1)
                    remaining = total - idx + 1
                    eta_seconds = avg_time * remaining
                    eta_str = f"{int(eta_seconds // 60)}m {int(eta_seconds % 60)}s"
                    logger.info(f"[{idx}/{total}] ~{eta_str} remaining")
                else:
                    logger.info(f"[{idx}/{total}]")

                logger.info(f"Correcting title for: {listing.original_title}")

                corrected_title = await correct_title_with_llm(listing.original_title)

                if corrected_title and corrected_title != listing.original_title:
                    stmt = (
                        update(Listing)
                        .where(Listing.id == listing.id)
                        .values(title=corrected_title)
                    )
                    await session.execute(stmt)
                    await session.commit()

                    logger.info(f"Corrected title to: {corrected_title}")
                    processed += 1
                else:
                    logger.info("Title did not need correction or correction failed.")

                # Delay between requests
                await asyncio.sleep(delay + random.uniform(0, 0.5))

            except Exception as e:
                logger.error(f"Error correcting title for {listing.original_title}: {e}")
                errors += 1
                await session.rollback()
                continue

        elapsed = time.time() - start_time
        elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"

        logger.info("Completed in %s", elapsed_str)
        logger.info(f"Processed: {processed}")
        logger.info(f"Errors: {errors}")
        logger.info(f"Total: {total}")
