from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional
from app.database import get_db
from app.models.log_entry import LogEntry

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("")
async def list_logs(
    level: Optional[str] = Query(None),
    service: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    query = select(LogEntry).order_by(desc(LogEntry.created_at))
    if level:
        query = query.where(LogEntry.level == level.upper())
    if service:
        query = query.where(LogEntry.service == service)
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    logs = result.scalars().all()
    return [
        {"id": l.id, "level": l.level, "service": l.service, "message": l.message, "context": l.context, "created_at": l.created_at}
        for l in logs
    ]
