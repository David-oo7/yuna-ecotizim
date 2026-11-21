"""Telegram webhook va chat sozlamalari."""

import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.deps import AppError, get_current_user
from app.models import TelegramChat, User
from app.services.telegram_service import handle_update

logger = logging.getLogger(__name__)

router = APIRouter(tags=["telegram"])


@router.post("/telegram/webhook/{secret}")
async def webhook(secret: str, request: Request, db: AsyncSession = Depends(get_db)) -> dict:
    expected = settings.telegram_webhook_secret
    header_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if not expected or secret != expected or (header_secret and header_secret != expected):
        raise AppError(403, "FORBIDDEN", "Webhook siri xato.")

    update = await request.json()
    try:
        await handle_update(db, update)
    except Exception:  # Telegram'ga doim 200 qaytaramiz, aks holda qayta yuboradi
        logger.exception("Telegram update bajarilmadi")
    return {"ok": True}


@router.get("/telegram/chats")
async def list_chats(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> dict:
    result = await db.execute(select(TelegramChat).order_by(TelegramChat.last_message_at.desc()))
    items = [
        {
            "chat_id": row.chat_id,
            "mode": row.mode,
            "is_blocked": row.is_blocked,
            "memory_summary": row.memory_summary,
        }
        for row in result.scalars().all()
    ]
    return {"items": items, "next_cursor": None}


@router.patch("/telegram/chats/{chat_id}")
async def update_chat(
    chat_id: int,
    payload: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(TelegramChat).where(TelegramChat.chat_id == chat_id))
    chat = result.scalar_one_or_none()
    if chat is None:
        raise AppError(404, "NOT_FOUND", "Chat topilmadi.")
    if payload.get("mode") in {"auto", "manual"}:
        chat.mode = payload["mode"]
    if "is_blocked" in payload:
        chat.is_blocked = bool(payload["is_blocked"])
    await db.commit()
    return {"chat_id": chat.chat_id, "mode": chat.mode, "is_blocked": chat.is_blocked}
