"""Eslatmalar CRUD."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import AppError, get_current_user
from app.models import Reminder, User
from app.schemas import ReminderIn, ReminderOut, ReminderUpdate
from app.services import reminder_service

router = APIRouter(tags=["reminders"])


@router.get("/reminders")
async def list_reminders(
    status: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    query = select(Reminder).where(Reminder.user_id == user.id)
    if status:
        query = query.where(Reminder.status == status)
    result = await db.execute(query.order_by(Reminder.remind_at))
    items = [ReminderOut.model_validate(r) for r in result.scalars().all()]
    return {"items": items, "next_cursor": None}


@router.post("/reminders", response_model=ReminderOut, status_code=201)
async def create_reminder(
    payload: ReminderIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReminderOut:
    reminder = await reminder_service.create(
        db,
        user,
        text=payload.text,
        when=payload.when,
        remind_at=payload.remind_at,
        repeat_rule=payload.repeat_rule,
        channel=payload.channel,
    )
    await db.commit()
    await db.refresh(reminder)
    return ReminderOut.model_validate(reminder)


@router.patch("/reminders/{reminder_id}", response_model=ReminderOut)
async def update_reminder(
    reminder_id: int,
    payload: ReminderUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReminderOut:
    reminder = await db.get(Reminder, reminder_id)
    if reminder is None or reminder.user_id != user.id:
        raise AppError(404, "NOT_FOUND", "Eslatma topilmadi.")
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        if value is not None:
            setattr(reminder, field, value)
    await db.commit()
    await db.refresh(reminder)
    return ReminderOut.model_validate(reminder)


@router.delete("/reminders/{reminder_id}", status_code=204)
async def delete_reminder(
    reminder_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    reminder = await db.get(Reminder, reminder_id)
    if reminder is None or reminder.user_id != user.id:
        raise AppError(404, "NOT_FOUND", "Eslatma topilmadi.")
    reminder.status = "cancelled"
    await db.commit()
