import uuid
from datetime import datetime
from sqlalchemy import String, Numeric, Integer, Text, Enum as SAEnum, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
import enum


class OrderStatus(str, enum.Enum):
    pending = "pending"
    filled = "filled"
    failed = "failed"
    cancelled = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id: Mapped[str] = mapped_column(String(36), ForeignKey("dca_plans.id"))
    exchange: Mapped[str] = mapped_column(String(20))
    symbol: Mapped[str] = mapped_column(String(20))
    side: Mapped[str] = mapped_column(String(10), default="buy")
    quote_amount: Mapped[float] = mapped_column(Numeric(18, 8))
    base_amount: Mapped[float | None] = mapped_column(Numeric(18, 8), nullable=True)
    price: Mapped[float | None] = mapped_column(Numeric(18, 8), nullable=True)
    cost_per_token: Mapped[float | None] = mapped_column(Numeric(18, 8), nullable=True)
    thb_usd_rate: Mapped[float | None] = mapped_column(Numeric(18, 8), nullable=True)
    exchange_order_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[OrderStatus] = mapped_column(SAEnum(OrderStatus), default=OrderStatus.pending)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    executed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
