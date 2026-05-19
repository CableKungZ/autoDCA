from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
import redis.asyncio as aioredis
import structlog

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.dca_plan import DcaPlan, PlanStatus
from app.services.dca_engine import execute_dca_plan
from app.services.rate_fetcher import fetch_and_store_rate

logger = structlog.get_logger()
settings = get_settings()


async def run_dca_job(plan_id: str) -> None:
    redis_client = aioredis.from_url(settings.redis_url)
    try:
        async with AsyncSessionLocal() as db:
            await execute_dca_plan(plan_id, db, redis_client)
    finally:
        await redis_client.aclose()


async def run_rate_fetch_job() -> None:
    async with AsyncSessionLocal() as db:
        await fetch_and_store_rate(db)


async def sync_plan_jobs(scheduler: AsyncIOScheduler) -> None:
    """Load all active plans from DB and add/update their cron jobs."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(DcaPlan).where(DcaPlan.status == PlanStatus.active)
        )
        plans = result.scalars().all()

    existing_job_ids = {job.id for job in scheduler.get_jobs()}

    for plan in plans:
        job_id = f"dca_{plan.id}"
        parts = plan.schedule_cron.split()
        trigger = CronTrigger(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            day_of_week=parts[4],
        )

        existing_job = scheduler.get_job(job_id)
        if existing_job:
            # Check if cron changed by comparing trigger fields
            existing_trigger = existing_job.trigger
            new_fields = {f.name: str(f) for f in trigger.fields if not f.is_default}
            old_fields = {f.name: str(f) for f in existing_trigger.fields if not f.is_default}
            if new_fields != old_fields:
                scheduler.reschedule_job(job_id, trigger=trigger)
                logger.info("job_rescheduled", plan_id=plan.id, cron=plan.schedule_cron)
        else:
            scheduler.add_job(
                run_dca_job,
                trigger=trigger,
                args=[plan.id],
                id=job_id,
                replace_existing=True,
            )
            logger.info("job_added", plan_id=plan.id, cron=plan.schedule_cron)

    # Remove jobs for plans no longer active
    active_ids = {f"dca_{p.id}" for p in plans}
    for job in scheduler.get_jobs():
        if job.id.startswith("dca_") and job.id not in active_ids:
            scheduler.remove_job(job.id)
            logger.info("job_removed", job_id=job.id)


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    # Rate fetch every hour
    scheduler.add_job(run_rate_fetch_job, CronTrigger(minute=0), id="rate_fetch", replace_existing=True)

    # Sync plan jobs every 5 minutes (picks up new/paused/deleted plans)
    scheduler.add_job(
        sync_plan_jobs,
        CronTrigger(minute="*/5"),
        args=[scheduler],
        id="sync_jobs",
        replace_existing=True,
    )

    return scheduler
