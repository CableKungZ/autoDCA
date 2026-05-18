import asyncio
import structlog

from app.scheduler.jobs import create_scheduler, sync_plan_jobs
from app.services.rate_fetcher import fetch_and_store_rate
from app.database import AsyncSessionLocal

logger = structlog.get_logger()


async def main() -> None:
    scheduler = create_scheduler()
    scheduler.start()
    logger.info("scheduler_started")

    # Initial sync and rate fetch
    async with AsyncSessionLocal() as db:
        await fetch_and_store_rate(db)
    await sync_plan_jobs(scheduler)

    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("scheduler_stopped")


if __name__ == "__main__":
    asyncio.run(main())
