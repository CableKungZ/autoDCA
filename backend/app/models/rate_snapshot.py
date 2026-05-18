from datetime import datetime
from sqlalchemy import Numeric, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class RateSnapshot(Base):
    __tablename__ = "rate_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rate: Mapped[float] = mapped_column(Numeric(18, 8))
    source: Mapped[str] = mapped_column(String(50), default="bitkub")
    recorded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
