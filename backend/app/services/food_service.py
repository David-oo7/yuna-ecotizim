"""Oziq-ovqat hisobi: yozuv qo'shish va kunlik jamlash."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FoodLog, User
from app.services.reminder_service import user_tz


async def add_items(
    db: AsyncSession, user: User, items: list[dict[str, Any]], source: str = "text"
) -> list[FoodLog]:
    created: list[FoodLog] = []
    for item in items[:20]:
        name = str(item.get("name") or "taom").strip()[:200]
        log = FoodLog(
            user_id=user.id,
            eaten_at=datetime.now(timezone.utc),
            meal_type=str(item.get("meal_type") or "snack"),
            name=name,
            amount_text=(str(item.get("amount_text"))[:80] if item.get("amount_text") else None),
            grams=float(item["grams"]) if item.get("grams") else None,
            kcal=float(item.get("kcal") or 0),
            protein=float(item.get("protein") or 0),
            fat=float(item.get("fat") or 0),
            carbs=float(item.get("carbs") or 0),
            source=source,
            confidence=str(item.get("confidence") or "medium"),
        )
        db.add(log)
        created.append(log)
    await db.flush()
    return created


def day_bounds(day: date, tz_name: str) -> tuple[datetime, datetime]:
    """Mahalliy kunning UTC chegaralari."""
    try:
        from zoneinfo import ZoneInfo

        tz = ZoneInfo(tz_name or "Asia/Tashkent")
    except Exception:
        tz = timezone(timedelta(hours=5))
    start_local = datetime.combine(day, time.min, tzinfo=tz)
    return start_local.astimezone(timezone.utc), (start_local + timedelta(days=1)).astimezone(
        timezone.utc
    )


async def summary(db: AsyncSession, user: User, day: date) -> dict[str, Any]:
    tz = user_tz(user)
    start, end = day_bounds(day, str(tz))
    result = await db.execute(
        select(FoodLog).where(
            FoodLog.user_id == user.id, FoodLog.eaten_at >= start, FoodLog.eaten_at < end
        )
    )
    logs = list(result.scalars().all())

    totals = {"kcal": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}
    meals: dict[str, dict[str, Any]] = {}
    for log in logs:
        totals["kcal"] += float(log.kcal)
        totals["protein"] += float(log.protein)
        totals["fat"] += float(log.fat)
        totals["carbs"] += float(log.carbs)
        bucket = meals.setdefault(log.meal_type, {"meal_type": log.meal_type, "items": 0, "kcal": 0.0})
        bucket["items"] += 1
        bucket["kcal"] += float(log.kcal)

    return {
        "date": day,
        "goal_kcal": user.kcal_goal,
        "totals": {k: round(v, 1) for k, v in totals.items()},
        "meals": sorted(meals.values(), key=lambda m: m["meal_type"]),
    }
