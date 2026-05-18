from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.dca_plan import DcaPlan, PlanStatus
from app.models.order import Order, OrderStatus
from app.services.exchange import fetch_ticker_price
import structlog

logger = structlog.get_logger()


async def get_plan_stats(plan: DcaPlan, db: AsyncSession) -> dict:
    result = await db.execute(
        select(Order).where(
            Order.plan_id == plan.id,
            Order.status == OrderStatus.filled,
        )
    )
    orders = result.scalars().all()

    # Only count orders where coins were actually received (base_amount > 0)
    valid_orders = [o for o in orders if o.base_amount and float(o.base_amount) > 0]
    total_invested = sum(float(o.quote_amount) for o in valid_orders)
    total_coins = sum(float(o.base_amount) for o in valid_orders)
    avg_cost = total_invested / total_coins if total_coins > 0 else 0

    current_price = 0.0
    try:
        current_price = await fetch_ticker_price(plan.exchange.value, plan.symbol)
    except Exception as e:
        logger.warning("fetch_price_failed", plan_id=plan.id, error=str(e))

    unrealized_pnl = (current_price - avg_cost) * total_coins if avg_cost > 0 else 0
    unrealized_pnl_pct = ((current_price - avg_cost) / avg_cost * 100) if avg_cost > 0 else 0

    return {
        "plan_id": plan.id,
        "name": plan.name,
        "exchange": plan.exchange.value,
        "symbol": plan.symbol,
        "currency": plan.currency,
        "avg_cost": avg_cost,
        "total_invested": total_invested,
        "total_coins": total_coins,
        "current_price": current_price,
        "unrealized_pnl": unrealized_pnl,
        "unrealized_pnl_pct": unrealized_pnl_pct,
        "order_count": len(orders),
    }


async def get_all_plan_stats(db: AsyncSession, symbol: str | None = None, exchange: str | None = None) -> list[dict]:
    query = select(DcaPlan).where(DcaPlan.status != PlanStatus.deleted)
    if symbol:
        query = query.where(DcaPlan.symbol.ilike(f"%{symbol}%"))
    if exchange:
        query = query.where(DcaPlan.exchange == exchange)

    result = await db.execute(query)
    plans = result.scalars().all()

    stats = []
    for plan in plans:
        s = await get_plan_stats(plan, db)
        stats.append(s)
    return stats
