import uuid
from datetime import datetime
from sqlalchemy import String, Numeric, Integer, Enum as SAEnum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
import enum


class Exchange(str, enum.Enum):
    binance = "binance"
    bitkub = "bitkub"


class PlanStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    deleted = "deleted"


class DcaPlan(Base):
    __tablename__ = "dca_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100))
    exchange: Mapped[Exchange] = mapped_column(SAEnum(Exchange))
    symbol: Mapped[str] = mapped_column(String(20))
    quote_amount: Mapped[float] = mapped_column(Numeric(18, 8))
    currency: Mapped[str] = mapped_column(String(10))
    schedule_cron: Mapped[str] = mapped_column(String(50))
    status: Mapped[PlanStatus] = mapped_column(SAEnum(PlanStatus), default=PlanStatus.active)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
