from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class OrderResponse(BaseModel):
    id: str
    plan_id: str
    exchange: str
    symbol: str
    side: str
    quote_amount: float
    base_amount: Optional[float]
    price: Optional[float]
    cost_per_token: Optional[float]
    thb_usd_rate: Optional[float]
    exchange_order_id: Optional[str]
    status: str
    retry_count: int
    error_message: Optional[str]
    executed_at: datetime

    class Config:
        from_attributes = True
