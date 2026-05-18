from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import date, timedelta
from typing import Optional
from app.database import get_db
from app.models.rate_snapshot import RateSnapshot

router = APIRouter(prefix="/api/rates", tags=["rates"])


@router.get("")
async def list_rates(
    days: int = Query(30, le=365),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime
    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(RateSnapshot)
        .where(RateSnapshot.recorded_at >= since)
        .order_by(RateSnapshot.recorded_at)
    )
    snapshots = result.scalars().all()
    return [{"rate": float(s.rate), "recorded_at": s.recorded_at, "source": s.source} for s in snapshots]


@router.get("/current")
async def current_rate(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RateSnapshot).order_by(desc(RateSnapshot.recorded_at)).limit(1)
    )
    snapshot = result.scalar_one_or_none()
    if not snapshot:
        return {"rate": None, "recorded_at": None}
    return {"rate": float(snapshot.rate), "recorded_at": snapshot.recorded_at, "source": snapshot.source}
