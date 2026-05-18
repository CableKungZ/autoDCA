import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.dca_plan import DcaPlan, PlanStatus
from app.schemas.plan import PlanCreate, PlanUpdate, PlanResponse
from app.services.exchange import _binance_request, _bitkub_request, _bitkub_ticker_items

router = APIRouter(prefix="/api/plans", tags=["plans"])


@router.get("/symbols")
async def list_symbols(exchange: str = Query(...)):
    """Return available trading symbols for the given exchange."""
    if exchange == "binance":
        data = await _binance_request("GET", "/api/v3/exchangeInfo")
        formatted = []
        for s in data.get("symbols", []):
            if s["status"] != "TRADING":
                continue
            if s["quoteAsset"] == "USDT":
                formatted.append(f"{s['baseAsset']}/USDT")
        return sorted(set(formatted))

    if exchange == "bitkub":
        data = await _bitkub_request("GET", "/api/v3/market/ticker")
        return sorted(
            t["symbol"].replace("_", "/") for t in _bitkub_ticker_items(data) if t.get("symbol", "").endswith("_THB")
        )

    raise HTTPException(400, f"Unsupported exchange: {exchange}")


@router.get("", response_model=list[PlanResponse])
async def list_plans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DcaPlan).where(DcaPlan.status != PlanStatus.deleted).order_by(DcaPlan.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=PlanResponse, status_code=201)
async def create_plan(body: PlanCreate, db: AsyncSession = Depends(get_db)):
    plan = DcaPlan(id=str(uuid.uuid4()), **body.model_dump())
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(plan_id: str, db: AsyncSession = Depends(get_db)):
    plan = await _get_or_404(plan_id, db)
    return plan


@router.patch("/{plan_id}", response_model=PlanResponse)
async def update_plan(plan_id: str, body: PlanUpdate, db: AsyncSession = Depends(get_db)):
    plan = await _get_or_404(plan_id, db)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(plan, k, v)
    await db.commit()
    await db.refresh(plan)
    return plan


@router.post("/{plan_id}/pause", response_model=PlanResponse)
async def pause_plan(plan_id: str, db: AsyncSession = Depends(get_db)):
    plan = await _get_or_404(plan_id, db)
    plan.status = PlanStatus.paused
    await db.commit()
    await db.refresh(plan)
    return plan


@router.post("/{plan_id}/resume", response_model=PlanResponse)
async def resume_plan(plan_id: str, db: AsyncSession = Depends(get_db)):
    plan = await _get_or_404(plan_id, db)
    plan.status = PlanStatus.active
    await db.commit()
    await db.refresh(plan)
    return plan


@router.delete("/{plan_id}", status_code=204)
async def delete_plan(plan_id: str, db: AsyncSession = Depends(get_db)):
    plan = await _get_or_404(plan_id, db)
    plan.status = PlanStatus.deleted
    await db.commit()


@router.post("/{plan_id}/trigger", status_code=202)
async def trigger_now(plan_id: str, db: AsyncSession = Depends(get_db)):
    """Manually trigger a DCA buy now."""
    from app.config import get_settings
    from app.services.dca_engine import execute_dca_plan
    import redis.asyncio as aioredis

    plan = await _get_or_404(plan_id, db)
    if plan.status != PlanStatus.active:
        raise HTTPException(400, "Plan is not active")

    settings = get_settings()
    redis_client = aioredis.from_url(settings.redis_url)
    try:
        await execute_dca_plan(plan_id, db, redis_client)
    except RuntimeError as e:
        raise HTTPException(409, str(e))
    finally:
        await redis_client.aclose()
    return {"message": "DCA order triggered"}


@router.post("/{plan_id}/release-lock", status_code=200)
async def release_lock(plan_id: str):
    """Force-release the Redis DCA lock for a plan (use when lock is stuck)."""
    import redis.asyncio as aioredis
    from app.config import get_settings
    settings = get_settings()
    redis_client = aioredis.from_url(settings.redis_url)
    try:
        deleted = await redis_client.delete(f"dca_lock:{plan_id}")
        return {"released": bool(deleted)}
    finally:
        await redis_client.aclose()


async def _get_or_404(plan_id: str, db: AsyncSession) -> DcaPlan:
    result = await db.execute(
        select(DcaPlan).where(DcaPlan.id == plan_id, DcaPlan.status != PlanStatus.deleted)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, "Plan not found")
    return plan
