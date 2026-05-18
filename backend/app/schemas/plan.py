from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PlanCreate(BaseModel):
    name: str
    exchange: str
    symbol: str
    quote_amount: float
    currency: str
    schedule_cron: str
    max_retries: int = 3


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    quote_amount: Optional[float] = None
    schedule_cron: Optional[str] = None
    max_retries: Optional[int] = None


class PlanResponse(BaseModel):
    id: str
    name: str
    exchange: str
    symbol: str
    quote_amount: float
    currency: str
    schedule_cron: str
    status: str
    max_retries: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
