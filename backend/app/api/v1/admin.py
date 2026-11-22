"""Admin paneli: foydalanuvchilar ro'yxati va umumiy statistika."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_admin
from app.models import ChatSession, Device, FoodLog, Message, Reminder, User
from app.schemas import AdminStats, AdminUserOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
async def list_users(
    limit: int = Query(default=100, ge=1, le=500),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    rows = await db.execute(select(User).order_by(User.created_at.desc()).limit(limit))
    users = [AdminUserOut.model_validate(u) for u in rows.scalars().all()]
    return {"items": users, "total": len(users)}


@router.get("/stats", response_model=AdminStats)
async def stats(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminStats:
    async def count(model) -> int:
        result = await db.execute(select(func.count()).select_from(model))
        return int(result.scalar() or 0)

    return AdminStats(
        users=await count(User),
        devices=await count(Device),
        sessions=await count(ChatSession),
        messages=await count(Message),
        reminders=await count(Reminder),
        food_logs=await count(FoodLog),
    )


__all__ = ["router"]
