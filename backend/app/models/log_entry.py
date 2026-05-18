from datetime import datetime
from sqlalchemy import String, Text, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class LogEntry(Base):
    __tablename__ = "log_entries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    level: Mapped[str] = mapped_column(String(20))
    service: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(Text)
    context: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
