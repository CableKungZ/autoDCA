from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from app.config import get_settings
import structlog

logger = structlog.get_logger()
settings = get_settings()


def get_bot() -> Bot:
    return Bot(token=settings.telegram_bot_token)


async def send_message(text: str, chat_id: str | None = None) -> None:
    if not settings.telegram_bot_token:
        return
    target = chat_id or settings.telegram_chat_id
    if not target:
        return
    bot = get_bot()
    try:
        await bot.send_message(chat_id=target, text=text, parse_mode="HTML")
    except Exception as e:
        logger.error("telegram_send_failed", error=str(e))


async def notify_order_success(order_data: dict) -> None:
    text = (
        f"✅ <b>DCA Order Filled</b>\n"
        f"Exchange: {order_data['exchange'].upper()}\n"
        f"Pair: {order_data['symbol']}\n"
        f"Spent: {order_data['quote_amount']} {order_data['currency']}\n"
        f"Received: {order_data['base_amount']:.8f} {order_data['symbol'].split('/')[0]}\n"
        f"Price: {order_data['price']:,.2f}\n"
        f"Cost/Token: {order_data['cost_per_token']:,.2f}\n"
        f"THB/USDT Rate: {order_data.get('thb_usd_rate', 'N/A')}"
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
    await send_message(text)


async def build_summary_text(plans_stats: list[dict], label: str = "All Plans") -> str:
    if not plans_stats:
        return "No active plans found."
    lines = [f"📊 <b>DCA Summary — {label}</b>\n"]
    for s in plans_stats:
        pnl_emoji = "📈" if s.get("unrealized_pnl", 0) >= 0 else "📉"
        lines.append(
            f"<b>{s['name']}</b> ({s['exchange'].upper()} | {s['symbol']})\n"
            f"  Avg Cost: {s['avg_cost']:,.4f}\n"
            f"  Total Invested: {s['total_invested']:,.2f} {s['currency']}\n"
            f"  Holdings: {s['total_coins']:.8f}\n"
            f"  {pnl_emoji} Unrealized PnL: {s['unrealized_pnl']:+,.2f} ({s['unrealized_pnl_pct']:+.2f}%)\n"
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
