"""Vaqt matnini haqiqiy vaqtga aylantirish va eslatma xizmati."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Device, Reminder, User, utcnow

logger = logging.getLogger(__name__)

MONTHS = {
    "yanvar": 1, "fevral": 2, "mart": 3, "aprel": 4, "may": 5, "iyun": 6,
    "iyul": 7, "avgust": 8, "sentabr": 9, "sentyabr": 9, "oktabr": 10,
    "noyabr": 11, "dekabr": 12,
}


class TimeParseError(ValueError):
    pass


def user_tz(user: User) -> ZoneInfo:
    try:
        return ZoneInfo(user.timezone or "Asia/Tashkent")
    except Exception:
        return ZoneInfo("Asia/Tashkent")


def parse_when(when: str, tz: ZoneInfo, now: datetime | None = None) -> datetime:
    """Tabiiy matn yoki ISO vaqtni UTC datetime ga aylantiradi.

    Qo'llanadigan shakllar:
      - "in 5 minutes" / "5 daqiqadan keyin"
      - "in 2 hours" / "2 soatdan keyin"
      - "tomorrow 09:00" / "ertaga 09:00"
      - ISO: "2026-11-22T09:00:00+05:00"
    """
    now = now or datetime.now(timezone.utc)
    raw = (when or "").strip()
    low = raw.lower()

    # ISO
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=tz)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        pass

    match = re.search(r"(\d+)\s*(daqiqa|minut|minute)", low)
    if match:
        return now + timedelta(minutes=int(match.group(1)))

    match = re.search(r"(\d+)\s*(soat|hour)", low)
    if match:
        return now + timedelta(hours=int(match.group(1)))

    match = re.search(r"(\d{1,2})[:.](\d{2})", low)
    hour, minute = (int(match.group(1)), int(match.group(2))) if match else (9, 0)

    local_now = now.astimezone(tz)
    target_date = local_now.date()
    if "ertaga" in low or "tomorrow" in low:
        target_date = (local_now + timedelta(days=1)).date()
    elif "bugun" in low:
        target_date = local_now.date()

    local_dt = datetime.combine(target_date, datetime.min.time(), tzinfo=tz).replace(
        hour=hour, minute=minute
    )
    if local_dt <= local_now and "ertaga" not in low and "tomorrow" not in low:
        local_dt += timedelta(days=1)
    return local_dt.astimezone(timezone.utc)


def next_occurrence(moment: datetime, rule: str | None) -> datetime | None:
    if not rule:
        return None
    if rule == "daily":
        return moment + timedelta(days=1)
    if rule == "weekly":
        return moment + timedelta(days=7)
    if rule == "monthly":
        return moment + timedelta(days=30)
    return None


async def create(
    db: AsyncSession,
    user: User,
    text: str,
    *,
    when: str | None = None,
    remind_at: datetime | None = None,
    repeat_rule: str | None = None,
    channel: str = "both",
) -> Reminder:
    tz = user_tz(user)
    if remind_at is None:
        remind_at = parse_when(when or "5 daqiqadan keyin", tz)
    elif remind_at.tzinfo is None:
        remind_at = remind_at.replace(tzinfo=tz).astimezone(timezone.utc)

    reminder = Reminder(
        user_id=user.id,
        text=text.strip()[:500] or "Eslatma",
        remind_at=remind_at,
        repeat_rule=repeat_rule,
        channel=channel,
        status="pending",
    )
    db.add(reminder)
    await db.flush()
    return reminder


async def cancel_latest(db: AsyncSession, user: User) -> Reminder | None:
    result = await db.execute(
        select(Reminder)
        .where(Reminder.user_id == user.id, Reminder.status == "pending")
        .order_by(Reminder.remind_at)
        .limit(1)
    )
    reminder = result.scalar_one_or_none()
    if reminder:
        reminder.status = "cancelled"
        await db.flush()
    return reminder


async def due_now(db: AsyncSession, limit: int = 50) -> list[Reminder]:
    result = await db.execute(
        select(Reminder)
        .where(Reminder.status == "pending", Reminder.remind_at <= utcnow())
        .order_by(Reminder.remind_at)
        .limit(limit)
    )
    return list(result.scalars().all())


async def mark_sent(db: AsyncSession, reminder: Reminder) -> Reminder | None:
    """Yuborilgan deb belgilaydi; takrorlanish bo'lsa keyingi nusxani yaratadi."""
    reminder.status = "sent"
    reminder.last_sent_at = utcnow()
    following = None
    upcoming = next_occurrence(reminder.remind_at, reminder.repeat_rule)
    if upcoming is not None:
        following = Reminder(
            user_id=reminder.user_id,
            text=reminder.text,
            remind_at=upcoming,
            repeat_rule=reminder.repeat_rule,
            channel=reminder.channel,
            status="pending",
        )
        db.add(following)
    await db.flush()
    return following


async def user_devices(db: AsyncSession, user_id: int, kind: str | None = None) -> list[Device]:
    query = select(Device).where(Device.user_id == user_id)
    if kind:
        query = query.where(Device.type == kind)
    result = await db.execute(query)
    return list(result.scalars().all())
