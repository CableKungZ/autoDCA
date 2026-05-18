from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.database import get_db
from app.services.stats import get_all_plan_stats, get_plan_stats
from app.models.dca_plan import DcaPlan, PlanStatus
from sqlalchemy import select

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/summary")
async def summary(
    plan_id: Optional[str] = Query(None),
    exchange: Optional[str] = Query(None),
    symbol: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    if plan_id:
        result = await db.execute(select(DcaPlan).where(DcaPlan.id == plan_id))
        plan = result.scalar_one_or_none()
        if not plan:
            return []
        return [await get_plan_stats(plan, db)]
    return await get_all_plan_stats(db, symbol=symbol, exchange=exchange)


@router.get("/pnl")
async def pnl(
    exchange: Optional[str] = Query(None),
    symbol: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stats = await get_all_plan_stats(db, symbol=symbol, exchange=exchange)
    total_invested = sum(s["total_invested"] for s in stats)
    total_pnl = sum(s["unrealized_pnl"] for s in stats)
    return {
        "total_invested": total_invested,
        "total_unrealized_pnl": total_pnl,
        "plans": stats,
    }
