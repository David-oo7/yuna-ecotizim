"""Suhbatlar (sessiyalar) va qurilmalar orasida davom ettirish."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import AppError, get_current_user
from app.models import ChatSession, Message, User, utcnow
from app.schemas import MessageOut, SessionDetail, SessionOut
from app.services import ws_manager

router = APIRouter(tags=["sessions"])


@router.get("/sessions")
async def list_sessions(
    limit: int = Query(default=30, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user.id)
        .order_by(ChatSession.updated_at.desc())
        .limit(limit)
    )
    items = [SessionOut.model_validate(row) for row in result.scalars().all()]
    return {"items": items, "next_cursor": None}


@router.get("/sessions/{session_id}", response_model=SessionDetail)
async def get_session(
    session_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionDetail:
    session = await db.get(ChatSession, session_id)
    if session is None or session.user_id != user.id:
        raise AppError(404, "NOT_FOUND", "Suhbat topilmadi.")

    result = await db.execute(
        select(Message).where(Message.session_id == session.id).order_by(Message.id)
    )
    messages = [MessageOut.model_validate(m) for m in result.scalars().all()]
    detail = SessionDetail.model_validate(session)
    detail.messages = messages
    return detail


@router.patch("/sessions/{session_id}", response_model=SessionOut)
async def update_session(
    session_id: int,
    payload: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionOut:
    session = await db.get(ChatSession, session_id)
    if session is None or session.user_id != user.id:
        raise AppError(404, "NOT_FOUND", "Suhbat topilmadi.")
    if "title" in payload and payload["title"]:
        session.title = str(payload["title"])[:200]
    if payload.get("archived"):
        session.archived_at = utcnow()
    await db.commit()
    return SessionOut.model_validate(session)


@router.post("/sessions/{session_id}/handoff", response_model=SessionOut)
async def handoff(
    session_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionOut:
    """Sessiyani boshqa qurilmada davom ettirish belgisi."""
    session = await db.get(ChatSession, session_id)
    if session is None or session.user_id != user.id:
        raise AppError(404, "NOT_FOUND", "Suhbat topilmadi.")
    session.updated_at = utcnow()
    await db.commit()
    await ws_manager.manager.send_to_user(
        user.id, {"type": "session_switched", "session_id": session.id}
    )
    return SessionOut.model_validate(session)
