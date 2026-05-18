from sqlalchemy.ext.asyncio import AsyncSession
from app.models.rate_snapshot import RateSnapshot
from app.services.exchange import fetch_thb_usdt_rate
import structlog

logger = structlog.get_logger()


async def fetch_and_store_rate(db: AsyncSession) -> float | None:
    try:
        rate = await fetch_thb_usdt_rate()
    except Exception as e:
        logger.warning("fetch_thb_usdt_rate_failed", error=str(e))
        return None
    snapshot = RateSnapshot(rate=rate, source="bitkub")
    db.add(snapshot)
    await db.commit()
    logger.info("rate_snapshot_saved", rate=rate)
    return rate


async def get_latest_rate(db: AsyncSession) -> float | None:
    from sqlalchemy import select, desc
    result = await db.execute(
        select(RateSnapshot).order_by(desc(RateSnapshot.recorded_at)).limit(1)
    )
    snapshot = result.scalar_one_or_none()
    return float(snapshot.rate) if snapshot else None
