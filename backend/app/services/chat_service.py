"""Suhbat mantiqi — /chat, /voice/chat va Telegram bot shu funksiyani ishlatadi."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatSession, Device, Message, User, utcnow
from app.services import ai_service, intents, ws_manager


async def get_or_create_session(
    db: AsyncSession,
    user: User,
    session_id: int | None = None,
    device: Device | None = None,
    title: str | None = None,
) -> ChatSession:
    if session_id is not None:
        session = await db.get(ChatSession, session_id)
        if session is None or session.user_id != user.id:
            from app.deps import AppError

            raise AppError(404, "NOT_FOUND", "Suhbat topilmadi.")
        if device is not None:
            session.last_device_id = device.id
        return session

    session = ChatSession(
        user_id=user.id,
        title=(title or "Yangi suhbat")[:200],
        last_device_id=device.id if device else None,
        state_json={},
    )
    db.add(session)
    await db.flush()
    return session


async def history(db: AsyncSession, session: ChatSession, limit: int = 20) -> list[dict[str, str]]:
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session.id)
        .order_by(Message.id.desc())
        .limit(limit)
    )
    rows = list(result.scalars().all())
    rows.reverse()
    return [{"role": m.role, "content": m.content} for m in rows]


async def handle_message(
    db: AsyncSession,
    user: User,
    text: str,
    *,
    session_id: int | None = None,
    mode: str = "auto",
    device: Device | None = None,
    msg_type: str = "text",
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    session = await get_or_create_session(db, user, session_id, device)
    if session.title == "Yangi suhbat" and text:
        session.title = text.strip()[:60] or "Yangi suhbat"

    user_message = Message(
        session_id=session.id,
        user_id=user.id,
        role="user",
        type=msg_type,
        content=text,
        meta=meta or {},
    )
    db.add(user_message)
    await db.flush()

    past = await history(db, session)
    result = await ai_service.respond(text, past, mode=mode, user_name=user.name)
    applied = await intents.apply_actions(db, user, result.actions)

    assistant_message = Message(
        session_id=session.id,
        user_id=user.id,
        role="assistant",
        content=result.reply,
        meta={"actions": applied, "usage": result.usage},
    )
    db.add(assistant_message)
    session.updated_at = utcnow()
    await db.commit()

    await ws_manager.manager.send_to_user(
        user.id,
        {
            "type": "message",
            "session_id": session.id,
            "message": {
                "id": assistant_message.id,
                "role": "assistant",
                "content": result.reply,
                "created_at": assistant_message.created_at.isoformat(),
            },
        },
    )

    return {
        "session_id": session.id,
        "message_id": assistant_message.id,
        "reply": result.reply,
        "actions": applied,
        "usage": result.usage,
    }
