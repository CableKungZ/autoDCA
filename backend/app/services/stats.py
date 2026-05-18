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

    # Compute total_invested_thb for cross-currency normalization
    # For THB plans: direct. For USDT plans: multiply each order's quote by its stored rate.
    total_invested_thb = 0.0
    for o in valid_orders:
        if plan.currency == "THB":
            total_invested_thb += float(o.quote_amount)
        else:
            rate = float(o.thb_usd_rate) if o.thb_usd_rate else 0
            total_invested_thb += float(o.quote_amount) * rate

    current_price = 0.0
    try:
        current_price = await fetch_ticker_price(plan.exchange.value, plan.symbol)
    except Exception as e:
        logger.warning("fetch_price_failed", plan_id=plan.id, error=str(e))

    unrealized_pnl = (current_price - avg_cost) * total_coins if avg_cost > 0 else 0
    unrealized_pnl_pct = ((current_price - avg_cost) / avg_cost * 100) if avg_cost > 0 else 0

    # THB-normalized PnL
    from app.services.rate_fetcher import get_latest_rate
    latest_rate = await get_latest_rate(db) or 1.0
    if plan.currency == "THB":
        unrealized_pnl_thb = unrealized_pnl
        current_price_thb = current_price
        avg_cost_thb = avg_cost
    else:
        unrealized_pnl_thb = unrealized_pnl * latest_rate
        current_price_thb = current_price * latest_rate
        avg_cost_thb = avg_cost * latest_rate

    return {
        "plan_id": plan.id,
        "name": plan.name,
        "exchange": plan.exchange.value,
        "symbol": plan.symbol,
        "currency": plan.currency,
        "avg_cost": avg_cost,
        "avg_cost_thb": avg_cost_thb,
        "total_invested": total_invested,
        "total_invested_thb": total_invested_thb,
        "total_coins": total_coins,
        "current_price": current_price,
        "current_price_thb": current_price_thb,
        "unrealized_pnl": unrealized_pnl,
        "unrealized_pnl_thb": unrealized_pnl_thb,
        "unrealized_pnl_pct": unrealized_pnl_pct,
        "order_count": len(orders),
        "thb_rate": latest_rate,
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
