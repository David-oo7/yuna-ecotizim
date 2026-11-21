"""Rejali vazifalar: eslatmalarni yetkazish va kundalik maslahat."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.db import SessionLocal
from app.models import Reminder, User
from app.services import push_service, reminder_service, telegram_service, ws_manager
from app.services.advice_service import ensure_today_advice
from app.services.reminder_service import user_tz

logger = logging.getLogger(__name__)

scheduler: AsyncIOScheduler | None = None


async def deliver_due_reminders(session_factory=None) -> int:
    """Vaqti kelgan eslatmalarni uch kanalga yetkazadi. Nechta yuborildi."""
    sent = 0
    factory = session_factory or SessionLocal
    async with factory() as db:
        due = await reminder_service.due_now(db)
        for reminder in due:
            user = await db.get(User, reminder.user_id)
            if user is None:
                reminder.status = "failed"
                continue

            # Kechikish 5 daqiqadan ko'p bo'lsa — "kechikdim" izohi bilan
            late = (datetime.now(timezone.utc) - reminder.remind_at).total_seconds() > 300
            body = reminder.text + (" (kechikdim 🙏)" if late else "")

            delivered = await ws_manager.manager.send_to_user(
                user.id, {"type": "reminder", "text": body, "id": reminder.id}
            )

            if reminder.channel in {"push", "both"}:
                devices = await reminder_service.user_devices(db, user.id, "android")
                for device in devices:
                    if device.fcm_token:
                        ok = await push_service.send(
                            device.fcm_token, "Yuna eslatmasi", body, {"reminder_id": str(reminder.id)}
                        )
                        delivered += int(ok)

            if reminder.channel in {"telegram", "both"} and user.telegram_id:
                await telegram_service.send_message(int(user.telegram_id), f"⏰ {body}")
                delivered += 1

            await reminder_service.mark_sent(db, reminder)
            sent += 1

        await db.commit()
    return sent


async def send_daily_advice() -> int:
    """Mahalliy vaqt bo'yicha advice_time kelgan foydalanuvchilarga maslahat yuboradi."""
    count = 0
    async with SessionLocal() as db:
        result = await db.execute(select(User).where(User.is_active.is_(True)))
        users = list(result.scalars().all())
        for user in users:
            now_local = datetime.now(timezone.utc).astimezone(user_tz(user))
            if now_local.strftime("%H:%M") != user.advice_time.strftime("%H:%M"):
                continue

            advice = await ensure_today_advice(db, user)
            if advice.channels:  # allaqachon yuborilgan
                continue

            await ws_manager.manager.send_to_user(
                user.id, {"type": "advice", "text": advice.text}
            )
            devices = await reminder_service.user_devices(db, user.id, "android")
            for device in devices:
                if device.fcm_token:
                    await push_service.send(device.fcm_token, "Kunlik maslahat", advice.text)
            if user.telegram_id:
                await telegram_service.send_message(int(user.telegram_id), f"🌸 {advice.text}")

            advice.channels = ["push", "telegram", "ws"]
            count += 1

        await db.commit()
    return count


def start_scheduler() -> AsyncIOScheduler:
    global scheduler
    if scheduler is not None:
        return scheduler
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    scheduler.add_job(deliver_due_reminders, "interval", seconds=30, id="reminders")
    scheduler.add_job(send_daily_advice, "interval", seconds=60, id="advice")
    scheduler.start()
    logger.info("Scheduler ishga tushdi")
    return scheduler


def stop_scheduler() -> None:
    global scheduler
    if scheduler is not None:
        scheduler.shutdown(wait=False)
        scheduler = None


__all__ = [
    "deliver_due_reminders",
    "send_daily_advice",
    "start_scheduler",
    "stop_scheduler",
    "Reminder",
]
