import uuid
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as aioredis
import structlog

from app.config import get_settings
from app.models.dca_plan import DcaPlan, PlanStatus
from app.models.order import Order, OrderStatus
from app.services.exchange import place_market_buy, decrypt_secret
from app.services.rate_fetcher import fetch_and_store_rate, get_latest_rate
from app.services.telegram import notify_order_success, notify_order_failed

logger = structlog.get_logger()
settings = get_settings()

LOCK_TTL = 60  # seconds


async def execute_dca_plan(plan_id: str, db: AsyncSession, redis_client: aioredis.Redis) -> None:
    lock_key = f"dca_lock:{plan_id}"
    lock = redis_client.lock(lock_key, timeout=LOCK_TTL)

    acquired = await lock.acquire(blocking=False)
    if not acquired:
        logger.warning("dca_lock_not_acquired", plan_id=plan_id)
        raise RuntimeError(f"Plan {plan_id} is already executing (Redis lock held). Use /release-lock if stuck.")

    try:
        result = await db.execute(select(DcaPlan).where(DcaPlan.id == plan_id))
        plan = result.scalar_one_or_none()

        if not plan or plan.status != PlanStatus.active:
            logger.info("plan_not_active", plan_id=plan_id)
            return

        thb_rate = await get_latest_rate(db)
        if thb_rate is None:
            thb_rate = await fetch_and_store_rate(db)

        order = Order(
            id=str(uuid.uuid4()),
            plan_id=plan_id,
            exchange=plan.exchange.value,
            symbol=plan.symbol,
            quote_amount=float(plan.quote_amount),
            status=OrderStatus.pending,
            thb_usd_rate=thb_rate,
        )
        db.add(order)
        await db.commit()

        try:
            # Decrypt API keys from plan (keys stored encrypted in env for now)
            api_key = settings.binance_api_key if plan.exchange.value == "binance" else settings.bitkub_api_key
            api_secret = settings.binance_api_secret if plan.exchange.value == "binance" else settings.bitkub_api_secret

            raw_order = await place_market_buy(
                exchange=plan.exchange.value,
                symbol=plan.symbol,
                quote_amount=float(plan.quote_amount),
                api_key=api_key,
                api_secret=api_secret,
            )

            base_received = float(raw_order.get("base_received", 0))
            avg_price = float(raw_order.get("avg_price", 0))

            order.base_amount = base_received
            order.price = avg_price
            order.cost_per_token = avg_price
            order.exchange_order_id = str(raw_order.get("exchange_order_id", ""))
            order.status = OrderStatus.filled
            await db.commit()

            await notify_order_success({
                "exchange": plan.exchange.value,
                "symbol": plan.symbol,
                "quote_amount": float(plan.quote_amount),
                "currency": plan.currency,
                "base_amount": base_received,
                "price": avg_price,
                "cost_per_token": avg_price,
                "thb_usd_rate": thb_rate,
            })

        except Exception as e:
            order.retry_count += 1
            order.error_message = str(e)

            if order.retry_count >= plan.max_retries:
                order.status = OrderStatus.failed
                await db.commit()
                await notify_order_failed(
                    {"exchange": plan.exchange.value, "symbol": plan.symbol, "error_message": str(e)},
                    order.retry_count,
                    plan.max_retries,
                )
                logger.error("dca_order_failed_final", plan_id=plan_id, error=str(e))
            else:
                order.status = OrderStatus.pending
                await db.commit()
                await notify_order_failed(
                    {"exchange": plan.exchange.value, "symbol": plan.symbol, "error_message": str(e)},
                    order.retry_count,
                    plan.max_retries,
                )
                # Schedule retry in 5 minutes
                await asyncio.sleep(300)
                await execute_dca_plan(plan_id, db, redis_client)

    finally:
        try:
            await lock.release()
        except Exception:
            pass
