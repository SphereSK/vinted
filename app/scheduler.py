"""Cron scheduler for automated scraping tasks."""
import asyncio
import subprocess
from datetime import datetime
from crontab import CronTab
from sqlalchemy import select

from app.db.models import ScrapeConfig
from app.db.session import Session, init_db


def get_user_crontab():
    """Get the current user's crontab."""
    return CronTab(user=True)


async def sync_crontab():
    """
    Sync scrape configurations with system crontab.
    This function should be called whenever configs are created/updated/deleted.
    """
    await init_db()
    cron = get_user_crontab()

    # Remove all existing vinted-scraper jobs
    cron.remove_all(comment='vinted-scraper')

    # Get all active configs with cron schedules
    async with Session() as session:
        result = await session.execute(
            select(ScrapeConfig).where(
                ScrapeConfig.is_active == True,
                ScrapeConfig.cron_schedule.isnot(None)
            )
        )
        configs = result.scalars().all()

        # Add new jobs
        for config in configs:
            if config.cron_schedule:
                # Create cron command
                cmd = f"cd /home/datament/project/vinted && vinted-scraper scrape "
                cmd += f"--search-text '{config.search_text}' "
                cmd += f"--max-pages {config.max_pages} "
                cmd += f"--delay {config.delay} "

                if config.categories:
                    for cat_id in config.categories:
                        cmd += f"-c {cat_id} "

                if config.platform_ids:
                    for plat_id in config.platform_ids:
                        cmd += f"-p {plat_id} "

                if config.fetch_details:
                    cmd += "--fetch-details "

                cmd += "--no-proxy"

                # Add to crontab
                job = cron.new(command=cmd, comment=f'vinted-scraper-{config.id}')
                job.setall(config.cron_schedule)

    # Write to system
    cron.write()
    print(f"✅ Synced {len(configs)} cron jobs to system crontab")


async def list_scheduled_jobs():
    """List all scheduled vinted-scraper jobs."""
    cron = get_user_crontab()
    jobs = []

    for job in cron.find_comment('vinted-scraper'):
        jobs.append({
            'schedule': str(job.slices),
            'command': job.command,
            'enabled': job.is_enabled(),
            'comment': job.comment
        })

    return jobs


async def remove_all_jobs():
    """Remove all vinted-scraper cron jobs."""
    cron = get_user_crontab()
    count = cron.remove_all(comment='vinted-scraper')
    cron.write()
    print(f"✅ Removed {count} cron jobs")
    return count


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
            asyncio.run(remove_all_jobs())
    else:
        print("Usage: python -m app.scheduler [sync|list|clear]")
