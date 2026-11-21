"""Telegram bot mantiqi (aiogram 3 `Bot` orqali yuborish).

Webhook'dan kelgan update'ni qayta ishlaydi:
  - auto rejim: Yuna o'zi javob yozadi
  - manual rejim: javob varianti egasiga tasdiqlash uchun yuboriladi
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import TelegramChat, User
from app.ratelimit import check
from app.services import chat_service, persona

logger = logging.getLogger(__name__)

_pending: dict[int, dict[str, Any]] = {}  # xabar id -> {chat_id, reply, text}


def _bot():
    if not settings.telegram_bot_token:
        return None
    try:
        from aiogram import Bot

        return Bot(token=settings.telegram_bot_token)
    except ImportError:  # pragma: no cover
        logger.warning("aiogram o'rnatilmagan")
        return None


async def send_message(chat_id: int, text: str, buttons: list[list[dict]] | None = None) -> None:
    bot = _bot()
    if bot is None:
        logger.info("Telegram sozlanmagan, xabar yuborilmadi: %s", text[:60])
        return

    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    markup = None
    if buttons:
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text=b["text"], callback_data=b["data"])
                    for b in row
                ]
                for row in buttons
            ]
        )
    try:
        await bot.send_message(chat_id, text[:4000], reply_markup=markup)
    except Exception as exc:  # pragma: no cover
        logger.warning("Telegramga yuborilmadi: %s", exc)
    finally:
        await bot.session.close()


async def _owner(db: AsyncSession) -> User | None:
    """Asosiy foydalanuvchi (shaxsiy deploy uchun)."""
    result = await db.execute(select(User).where(User.is_active.is_(True)).order_by(User.id))
    return result.scalars().first()


async def _get_chat(db: AsyncSession, chat_id: int) -> TelegramChat:
    result = await db.execute(select(TelegramChat).where(TelegramChat.chat_id == chat_id))
    chat = result.scalar_one_or_none()
    if chat is None:
        chat = TelegramChat(chat_id=chat_id, mode="manual")
        db.add(chat)
        await db.flush()
    return chat


async def handle_update(db: AsyncSession, update: dict[str, Any]) -> None:
    if "callback_query" in update:
        await _handle_callback(db, update["callback_query"])
        return

    message = update.get("message") or update.get("edited_message")
    if not message:
        return

    chat_id = int(message["chat"]["id"])
    text = (message.get("text") or "").strip()
    if not text:
        return

    chat = await _get_chat(db, chat_id)
    chat.last_message_at = datetime.now(timezone.utc)
    await db.commit()

    if chat.is_blocked:
        return

    if not check(f"tg:{chat_id}", limit=20):
        await send_message(chat_id, "Biroz sekinlashamiz 🙂 Bir daqiqadan keyin yozing.")
        return

    if text.startswith("/start"):
        await send_message(
            chat_id, f"Salom! Men {persona.YUNA_DISPLAY_NAME}. Sizga qanday yordam beraman?"
        )
        return

    owner = chat.user_id and await db.get(User, chat.user_id)
    if owner is None:
        owner = await _owner(db)
        if owner is None:
            await send_message(chat_id, "Tizim hali sozlanmagan.")
            return
        chat.user_id = owner.id
        await db.commit()

    if chat.mode == "auto":
        reply = await chat_service.handle_message(db, owner, text)
        await send_message(chat_id, reply["reply"])
        return

    # manual: javob variantini egasiga tasdiqlash uchun yuboramiz
    preview = await chat_service.handle_message(db, owner, text)
    ticket = hash((chat_id, preview["message_id"])) % 10**9
    _pending[ticket] = {"chat_id": chat_id, "reply": preview["reply"]}
    await send_message(
        int(owner.telegram_id) if owner.telegram_id else chat_id,
        f"💬 Chat {chat_id}\nSavol: {text[:300]}\n\nJavob varianti:\n{preview['reply'][:1200]}",
        buttons=[[
            {"text": "✅ Yuborish", "data": f"send:{ticket}"},
            {"text": "❌ Rad", "data": f"drop:{ticket}"},
        ]],
    )


async def _handle_callback(db: AsyncSession, callback: dict[str, Any]) -> None:
    data = str(callback.get("data") or "")
    action, _, raw = data.partition(":")
    try:
        ticket = int(raw)
    except ValueError:
        return

    item = _pending.pop(ticket, None)
    if not item:
        return

    if action == "send":
        await send_message(int(item["chat_id"]), str(item["reply"]))
    await send_message(int(callback["message"]["chat"]["id"]), "Bajarildi.")


async def chat_count(db: AsyncSession) -> int:
    result = await db.execute(select(func.count(TelegramChat.id)))
    return int(result.scalar_one())
