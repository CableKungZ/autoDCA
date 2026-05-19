from fastapi import APIRouter, Depends, HTTPException, Query
from app.ws import manager as ws_manager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, delete
from typing import Optional
from datetime import date
from pydantic import BaseModel
from app.database import get_db
from app.models.order import Order, OrderStatus
from app.schemas.order import OrderResponse
import uuid

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.get("", response_model=list[OrderResponse])
async def list_orders(
    exchange: Optional[str] = Query(None),
    symbol: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    plan_id: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    sort_by: str = Query("executed_at"),
    sort_dir: str = Query("desc"),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    query = select(Order)
    if exchange:
        query = query.where(Order.exchange == exchange)
    if symbol:
        query = query.where(Order.symbol.ilike(f"%{symbol}%"))
    if status:
        query = query.where(Order.status == status)
    if plan_id:
        query = query.where(Order.plan_id == plan_id)
    if date_from:
        query = query.where(Order.executed_at >= date_from)
    if date_to:
        query = query.where(Order.executed_at <= date_to)

    col = getattr(Order, sort_by, Order.executed_at)
    query = query.order_by(desc(col) if sort_dir == "desc" else col)
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(404, "Order not found")
    return order


class SellRequest(BaseModel):
    plan_id: str
    order_type: str          # "market" | "limit" | "percent"
    base_amount: float | None = None     # for market/limit: units to sell
    percent: float | None = None         # for percent: 0-100
    limit_price: float | None = None     # for limit orders


@router.post("/sell", status_code=201)
async def place_sell_order(body: SellRequest, db: AsyncSession = Depends(get_db)):
    from app.models.dca_plan import DcaPlan, PlanStatus
    from app.services.exchange import place_sell, fetch_ticker_price
    from app.services.rate_fetcher import get_latest_rate
    from app.config import get_settings

    # Load plan
    result = await db.execute(select(DcaPlan).where(DcaPlan.id == body.plan_id, DcaPlan.status != PlanStatus.deleted))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, "Plan not found")

    settings = get_settings()
    api_key = settings.binance_api_key if plan.exchange.value == "binance" else settings.bitkub_api_key
    api_secret = settings.binance_api_secret if plan.exchange.value == "binance" else settings.bitkub_api_secret

    # Resolve amount
    sell_amount = body.base_amount
    if body.order_type == "percent":
        if not body.percent or body.percent <= 0 or body.percent > 100:
            raise HTTPException(400, "percent must be 1-100")
        # Sum filled base_amount for this plan
        res = await db.execute(
            select(Order).where(Order.plan_id == body.plan_id, Order.status == OrderStatus.filled, Order.side == "buy")
        )
        buy_orders = res.scalars().all()
        total_holdings = sum(float(o.base_amount or 0) for o in buy_orders)
        sell_amount = total_holdings * (body.percent / 100)
        if sell_amount <= 0:
            raise HTTPException(400, "No holdings to sell")

    if not sell_amount or sell_amount <= 0:
        raise HTTPException(400, "Invalid sell amount")

    order_type = "limit" if body.order_type == "limit" else "market"
    thb_rate = await get_latest_rate(db)

    order = Order(
        id=str(uuid.uuid4()),
        plan_id=body.plan_id,
        exchange=plan.exchange.value,
        symbol=plan.symbol,
        side="sell",
        quote_amount=sell_amount,
        status=OrderStatus.pending,
        thb_usd_rate=thb_rate,
    )
    db.add(order)
    await db.commit()

    try:
        raw = await place_sell(
            exchange=plan.exchange.value,
            symbol=plan.symbol,
            base_amount=sell_amount,
            api_key=api_key,
            api_secret=api_secret,
            order_type=order_type,
            limit_price=body.limit_price,
        )
        order.base_amount = raw.get("base_sold", sell_amount)
        order.price = raw.get("avg_price")
        order.cost_per_token = raw.get("avg_price")
        order.exchange_order_id = str(raw.get("exchange_order_id", ""))
        status_str = raw.get("status", "filled").lower()
        order.status = OrderStatus.filled if "fill" in status_str or status_str == "new" and order_type == "limit" else OrderStatus.filled
        if order_type == "limit":
            order.status = OrderStatus.pending  # limit orders sit open
        await db.commit()
        await db.refresh(order)
        await ws_manager.broadcast("order_filled", {"plan_id": body.plan_id, "symbol": plan.symbol, "side": "sell"})
        return {"message": "Sell order placed", "order_id": order.id, "status": order.status, "avg_price": raw.get("avg_price"), "base_sold": raw.get("base_sold")}
    except Exception as e:
        order.status = OrderStatus.failed
        order.error_message = str(e)
        await db.commit()
        raise HTTPException(500, f"Sell failed: {e}")


@router.post("/clear-pending", status_code=200)
async def clear_pending_orders(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).where(Order.status == OrderStatus.pending))
    orders = result.scalars().all()
    count = len(orders)
    for order in orders:
        await db.delete(order)
    await db.commit()
    return {"cleared": count}


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(order_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(404, "Order not found")
    if order.status != OrderStatus.pending:
        raise HTTPException(400, "Only pending orders can be cancelled")
    await db.delete(order)
    await db.commit()
    return order
