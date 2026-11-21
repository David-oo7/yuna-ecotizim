"""Kundalik maslahat."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import AdviceOut
from app.services import ai_service
from app.services.advice_service import ensure_today_advice

router = APIRouter(tags=["advice"])


@router.get("/advice/today", response_model=AdviceOut)
async def today(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> AdviceOut:
    advice = await ensure_today_advice(db, user)
    await db.commit()
    return AdviceOut(date=advice.log_date, text=advice.text)


__all__ = ["router", "ai_service", "datetime", "timezone"]
