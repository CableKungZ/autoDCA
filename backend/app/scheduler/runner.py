import asyncio
import structlog
import redis.asyncio as aioredis

from app.scheduler.jobs import create_scheduler, sync_plan_jobs
from app.services.rate_fetcher import fetch_and_store_rate
from app.database import AsyncSessionLocal, async_session_factory
from app.config import get_settings

logger = structlog.get_logger()


async def main() -> None:
    scheduler = create_scheduler()
    scheduler.start()
    logger.info("scheduler_started")

    # Initial sync and rate fetch
    async with AsyncSessionLocal() as db:
        await fetch_and_store_rate(db)
    await sync_plan_jobs(scheduler)

    # Start Telegram bot (polling) if configured
    tg_app = None
    try:
        from app.config import get_settings
        from app.services.telegram import start_bot
        settings = get_settings()
        if settings.telegram_bot_token:
            tg_app = await start_bot(async_session_factory)
            await tg_app.initialize()
            await tg_app.start()
            await tg_app.updater.start_polling(drop_pending_updates=True)
            logger.info("telegram_bot_started")
    except Exception as e:
        logger.warning("telegram_bot_start_failed", error=str(e))

    # Listen for immediate sync signals from API
    asyncio.create_task(_listen_sync(scheduler))

    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        if tg_app:
            await tg_app.updater.stop()
            await tg_app.stop()
            await tg_app.shutdown()
        scheduler.shutdown()
        logger.info("scheduler_stopped")


async def _listen_sync(scheduler):
    """Subscribe to Redis channel and re-sync jobs immediately when API signals."""
    settings = get_settings()
    r = aioredis.from_url(settings.redis_url)
    pubsub = r.pubsub()
    await pubsub.subscribe("scheduler:sync_now")
    logger.info("sync_listener_started")
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                logger.info("sync_now_received")
                await sync_plan_jobs(scheduler)
    except Exception as e:
        logger.warning("sync_listener_error", error=str(e))
    finally:
        await r.aclose()


if __name__ == "__main__":
    asyncio.run(main())
