"""Suhbat endpointlari: oddiy va oqimli javob."""

import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user, get_device
from app.models import Device, User
from app.ratelimit import ai_limit
from app.schemas import ChatIn, ChatOut
from app.services import chat_service

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatOut)
async def chat(
    payload: ChatIn,
    user: User = Depends(ai_limit),
    device: Device | None = Depends(get_device),
    db: AsyncSession = Depends(get_db),
) -> ChatOut:
    result = await chat_service.handle_message(
        db,
        user,
        payload.text,
        session_id=payload.session_id,
        mode=payload.mode,
        device=device,
    )
    return ChatOut(**result)


@router.post("/chat/stream")
async def chat_stream(
    payload: ChatIn,
    user: User = Depends(ai_limit),
    device: Device | None = Depends(get_device),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Server-Sent Events: tayyor javob bo'laklarga bo'lib yuboriladi.

    (Haqiqiy token oqimi OpenRouter streaming bilan 5-bosqichda qo'shiladi.)
    """
    result = await chat_service.handle_message(
        db,
        user,
        payload.text,
        session_id=payload.session_id,
        mode=payload.mode,
        device=device,
    )

    async def events():
        yield f"event: start\ndata: {json.dumps({'session_id': result['session_id']})}\n\n"
        reply = result["reply"]
        for index in range(0, len(reply), 120):
            chunk = reply[index : index + 120]
            yield f"event: chunk\ndata: {json.dumps({'text': chunk})}\n\n"
        yield f"event: done\ndata: {json.dumps({'message_id': result['message_id'], 'actions': result['actions']}, default=str)}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
