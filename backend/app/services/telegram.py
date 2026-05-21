import asyncio
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from app.config import get_settings
import structlog

logger = structlog.get_logger()
settings = get_settings()


def get_bot() -> Bot:
    return Bot(token=settings.telegram_bot_token)


async def send_message(text: str, chat_id: str | None = None, auto_delete_seconds: int | None = None) -> None:
    if not settings.telegram_bot_token:
        return
    target = chat_id or settings.telegram_chat_id
    if not target:
        return
    bot = get_bot()
    try:
        msg = await bot.send_message(chat_id=target, text=text, parse_mode="HTML")
        if auto_delete_seconds:
            asyncio.create_task(_delete_later(bot, target, msg.message_id, auto_delete_seconds))
    except Exception as e:
        logger.error("telegram_send_failed", error=str(e))


async def _delete_later(bot: Bot, chat_id: str, message_id: int, delay: int) -> None:
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass


async def notify_order_success(order_data: dict) -> None:
    currency = order_data.get('currency', 'USDT')
    quote = float(order_data['quote_amount'])
    rate = float(order_data.get('thb_usd_rate') or 0)
    base_token = order_data['symbol'].split('/')[0]
    price = float(order_data.get('price') or 0)

    # Cross-currency display: always show both THB and USDT
    if currency == 'THB':
        spent_str = f"{quote:,.2f} THB"
        spent_str += f" (≈ {quote/rate:,.2f} USDT)" if rate else ""
        price_str = f"{price:,.2f} THB"
    else:
        spent_str = f"{quote:,.2f} USDT"
        spent_str += f" (≈ {quote*rate:,.2f} THB)" if rate else ""
        price_str = f"{price:,.4f} USDT (≈ {price*rate:,.2f} THB)" if rate else f"{price:,.4f} USDT"

    text = (
        f"✅ <b>DCA Order Filled</b>\n"
        f"Exchange: {order_data['exchange'].upper()}\n"
        f"Pair: {order_data['symbol']}\n"
        f"Spent: {spent_str}\n"
        f"Received: {float(order_data['base_amount']):.8f} {base_token}\n"
        f"Price: {price_str}\n"
        f"Cost/Token: {float(order_data.get('cost_per_token') or 0):,.4f} {currency}\n"
        f"THB/USDT Rate: {rate:,.2f}"
    )
    await send_message(text)


async def notify_order_failed(order_data: dict, retry_count: int, max_retries: int) -> None:
    final = retry_count >= max_retries
    emoji = "❌" if final else "⚠️"
    status = "FINAL FAILURE" if final else f"retry {retry_count}/{max_retries}"
    text = (
        f"{emoji} <b>DCA Order Failed</b> ({status})\n"
        f"Exchange: {order_data['exchange'].upper()}\n"
        f"Pair: {order_data['symbol']}\n"
        f"Error: {order_data.get('error_message', 'Unknown error')}"
    )
    await send_message(text, auto_delete_seconds=5)


async def build_summary_text(plans_stats: list[dict], label: str = "All Plans") -> str:
    if not plans_stats:
        return "No active plans found."
    lines = [f"📊 <b>DCA Summary — {label}</b>\n"]
    for s in plans_stats:
        pnl = s.get("unrealized_pnl", 0)
        pnl_thb = s.get("unrealized_pnl_thb", 0)
        pnl_emoji = "📈" if pnl >= 0 else "📉"
        currency = s.get("currency", "USDT")
        rate = s.get("thb_rate", 0)

        # Avg cost with cross-currency
        avg = s.get("avg_cost", 0)
        avg_thb = s.get("avg_cost_thb", 0)
        if currency == "THB":
            avg_str = f"{avg:,.2f} THB (≈ {avg/rate:,.4f} USDT)" if rate else f"{avg:,.2f} THB"
        else:
            avg_str = f"{avg:,.4f} USDT (≈ {avg_thb:,.2f} THB)"

        # Invested with cross-currency
        invested = s.get("total_invested", 0)
        invested_thb = s.get("total_invested_thb", 0)
        if currency == "THB":
            inv_str = f"{invested:,.2f} THB (≈ {invested/rate:,.2f} USDT)" if rate else f"{invested:,.2f} THB"
        else:
            inv_str = f"{invested:,.2f} USDT (≈ {invested_thb:,.2f} THB)"

        # PnL with cross-currency
        if currency == "THB":
            pnl_str = f"{pnl:+,.2f} THB"
        else:
            pnl_str = f"{pnl:+,.4f} USDT (≈ {pnl_thb:+,.2f} THB)"

        lines.append(
            f"<b>{s['name']}</b> ({s['exchange'].upper()} | {s['symbol']})\n"
            f"  Avg Cost: {avg_str}\n"
            f"  Invested: {inv_str}\n"
            f"  Holdings: {s.get('total_coins', 0):.8f} {s['symbol'].split('/')[0]}\n"
            f"  {pnl_emoji} PnL: {pnl_str} ({s.get('unrealized_pnl_pct', 0):+.2f}%)\n"
        )
    return "\n".join(lines)


async def start_bot(db_session_factory) -> Application:
    app = Application.builder().token(settings.telegram_bot_token).build()

    async def cmd_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
        symbol_filter = context.args[0].upper() if context.args else None
        async with db_session_factory() as db:
            from app.services.stats import get_all_plan_stats
            stats = await get_all_plan_stats(db, symbol=symbol_filter)
            label = f"Symbol: {symbol_filter}" if symbol_filter else "All Plans"
            text = await build_summary_text(stats, label)
        await update.message.reply_text(text, parse_mode="HTML")

    async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
        async with db_session_factory() as db:
            from sqlalchemy import select
            from app.models.dca_plan import DcaPlan, PlanStatus
            result = await db.execute(
                select(DcaPlan).where(DcaPlan.status == PlanStatus.active)
            )
            plans = result.scalars().all()
        if not plans:
            await update.message.reply_text("No active DCA plans.")
            return
        lines = ["🟢 <b>Active DCA Plans</b>\n"]
        for p in plans:
            lines.append(f"• <b>{p.name}</b> — {p.exchange.upper()} {p.symbol} | {p.quote_amount} {p.currency} | {p.schedule_cron}")
        await update.message.reply_text("\n".join(lines), parse_mode="HTML")

    async def cmd_pnl(update: Update, context: ContextTypes.DEFAULT_TYPE):
        async with db_session_factory() as db:
            from app.services.stats import get_all_plan_stats
            stats = await get_all_plan_stats(db)
        text = await build_summary_text(stats, "PnL Summary")
        await update.message.reply_text(text, parse_mode="HTML")

    app.add_handler(CommandHandler("summary", cmd_summary))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("pnl", cmd_pnl))

    return app
