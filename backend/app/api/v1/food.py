"""Oziq-ovqat hisobi endpointlari."""

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import AppError, get_current_user
from app.models import FoodLog, User
from app.ratelimit import ai_limit
from app.schemas import FoodItemOut, FoodLogIn, FoodLogOut, FoodSummary
from app.services import ai_service, food_service, intents
from app.services.reminder_service import user_tz

router = APIRouter(tags=["food"])


def _local_today(user: User) -> date:
    return datetime.now(timezone.utc).astimezone(user_tz(user)).date()


@router.post("/food/log", response_model=FoodLogOut)
async def log_food(
    payload: FoodLogIn,
    user: User = Depends(ai_limit),
    db: AsyncSession = Depends(get_db),
) -> FoodLogOut:
    """Erkin matn: "tushlikda 1 kosa osh va non yedim"."""
    result = await ai_service.respond(payload.text, [], user_name=user.name)
    food_actions = [a for a in result.actions if a.get("type") == "food_log"]
    if not food_actions:
        return FoodLogOut(reply=result.reply, items=[])

    applied = await intents.apply_actions(db, user, food_actions)
    await db.commit()

    result_rows = await db.execute(
        select(FoodLog)
        .where(FoodLog.user_id == user.id)
        .order_by(FoodLog.id.desc())
        .limit(len(food_actions[0].get("payload", {}).get("items", [])) or 20)
    )
    logs = list(result_rows.scalars().all())
    items = [
        FoodItemOut(
            id=log.id,
            name=log.name,
            meal_type=log.meal_type,
            amount_text=log.amount_text,
            kcal=float(log.kcal),
            protein=float(log.protein),
            fat=float(log.fat),
            carbs=float(log.carbs),
        )
        for log in logs
    ]
    return FoodLogOut(reply=result.reply, items=items)


@router.get("/food/summary", response_model=FoodSummary)
async def food_summary(
    day: date | None = Query(default=None, alias="date"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FoodSummary:
    target = day or _local_today(user)
    data = await food_service.summary(db, user, target)
    return FoodSummary(**data)


@router.delete("/food/logs/{log_id}", status_code=204)
async def delete_food_log(
    log_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    log = await db.get(FoodLog, log_id)
    if log is None or log.user_id != user.id:
        raise AppError(404, "NOT_FOUND", "Yozuv topilmadi.")
    await db.delete(log)
    await db.commit()
