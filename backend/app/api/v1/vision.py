"""Rasm asosida tushuntirish."""

import asyncio
import io

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.deps import AppError, get_device
from app.models import Device, Message, User
from app.ratelimit import ai_limit
from app.schemas import VisionOut
from app.services import ai_service, chat_service, storage_service, ws_manager

router = APIRouter(tags=["vision"])

MAX_BYTES = 10 * 1024 * 1024


def _compress(data: bytes) -> tuple[bytes, str]:
    """Tezlik uchun rasmni kichraytiradi (uzun tomon 1600px)."""
    try:
        from PIL import Image

        image = Image.open(io.BytesIO(data)).convert("RGB")
        image.thumbnail((1600, 1600))
        buffer = io.BytesIO()
        image.save(buffer, "JPEG", quality=85)
        return buffer.getvalue(), "image/jpeg"
    except Exception:
        return data, "image/jpeg"


@router.post("/vision/explain", response_model=VisionOut)
async def explain(
    image: UploadFile = File(...),
    question: str | None = Form(default=None),
    session_id: int | None = Form(default=None),
    user: User = Depends(ai_limit),
    device: Device | None = Depends(get_device),
    db: AsyncSession = Depends(get_db),
) -> VisionOut:
    data = await image.read()
    if len(data) > MAX_BYTES:
        raise AppError(413, "FILE_TOO_LARGE", "Rasm 10 MB dan katta bo'lmasin.")
    if not data:
        raise AppError(422, "VALIDATION", "Rasm bo'sh.", "image")

    compressed, mime = await asyncio.to_thread(_compress, data)
    path, size = await storage_service.save_bytes(compressed, image.filename or "image.jpg", "images")

    session = await chat_service.get_or_create_session(db, user, session_id, device)
    db.add(
        Message(
            session_id=session.id,
            user_id=user.id,
            role="user",
            type="image",
            content=question or "Rasmni tushuntir",
            meta={"storage_path": path, "size": size, "mime": mime},
        )
    )
    await db.flush()

    reply = await ai_service.explain_image(compressed, question, user.name)

    db.add(
        Message(
            session_id=session.id,
            user_id=user.id,
            role="assistant",
            content=reply,
            meta={"source": "vision"},
        )
    )
    await db.commit()

    await ws_manager.manager.send_to_user(
        user.id, {"type": "message", "session_id": session.id, "message": {"role": "assistant", "content": reply}}
    )
    return VisionOut(session_id=session.id, reply=reply)


__all__ = ["router", "settings"]
