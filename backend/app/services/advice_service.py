"""Kundalik maslahat: yaratish va takrorlanmasligini ta'minlash."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AdviceLog, Reminder, User
from app.services import ai_service, food_service
from app.services.reminder_service import user_tz


def local_today(user: User) -> date:
    return datetime.now(timezone.utc).astimezone(user_tz(user)).date()


async def ensure_today_advice(db: AsyncSession, user: User) -> AdviceLog:
    today = local_today(user)
    result = await db.execute(
        select(AdviceLog).where(AdviceLog.user_id == user.id, AdviceLog.log_date == today)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    # Kontekst
    yesterday = today - timedelta(days=1)
    totals = (await food_service.summary(db, user, yesterday))["totals"]

    reminders = await db.execute(
        select(Reminder).where(
            Reminder.user_id == user.id,
            Reminder.status == "pending",
            Reminder.remind_at >= datetime.now(timezone.utc),
        )
    )
    pending_count = len(list(reminders.scalars().all()))

    recent_rows = await db.execute(
        select(AdviceLog)
        .where(AdviceLog.user_id == user.id)
        .order_by(AdviceLog.log_date.desc())
        .limit(7)
    )
    recent = [row.text for row in recent_rows.scalars().all()]

    text = await ai_service.daily_advice(user.name, totals, pending_count, recent)

    advice = AdviceLog(user_id=user.id, log_date=today, text=text, channels=[])
    db.add(advice)
    await db.flush()
    return advice
