"""Ovoz: STT, TTS va to'liq ovozli suhbat."""

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import AppError, get_current_user, get_device
from app.models import Device, User
from app.ratelimit import ai_limit
from app.schemas import ChatIn, SttOut, VoiceChatOut
from app.schemas import TtsIn, TtsOut
from app.services import audio_service, chat_service, storage_service

router = APIRouter(tags=["voice"])

MAX_AUDIO = 15 * 1024 * 1024


@router.post("/voice/stt", response_model=SttOut)
async def stt(
    audio: UploadFile = File(...),
    user: User = Depends(ai_limit),
) -> SttOut:
    data = await audio.read()
    if not data:
        raise AppError(422, "VALIDATION", "Audio bo'sh.", "audio")
    if len(data) > MAX_AUDIO:
        raise AppError(413, "FILE_TOO_LARGE", "Audio 15 MB dan katta bo'lmasin.")
    text = await audio_service.transcribe(data, audio.content_type or "audio/m4a")
    return SttOut(text=text)


@router.post("/voice/tts", response_model=TtsOut)
async def tts(payload: TtsIn, user: User = Depends(get_current_user)) -> TtsOut:
    audio, path = await audio_service.synthesize(payload.text)
    stored_path, _ = await storage_service.save_bytes(audio, "tts.mp3", "tts")
    return TtsOut(audio_url=storage_service.presigned_url(stored_path))


@router.post("/voice/chat", response_model=VoiceChatOut)
async def voice_chat(
    audio: UploadFile = File(...),
    session_id: str | None = Form(default=None),
    user: User = Depends(ai_limit),
    device: Device | None = Depends(get_device),
    db: AsyncSession = Depends(get_db),
) -> VoiceChatOut:
    data = await audio.read()
    if not data:
        raise AppError(422, "VALIDATION", "Audio bo'sh.", "audio")
    if len(data) > MAX_AUDIO:
        raise AppError(413, "FILE_TOO_LARGE", "Audio 15 MB dan katta bo'lmasin.")

    text = await audio_service.transcribe(data, audio.content_type or "audio/m4a")

    parsed_session: int | None = None
    if session_id and str(session_id).strip().isdigit():
        parsed_session = int(session_id)

    result = await chat_service.handle_message(
        db, user, text, session_id=parsed_session, device=device, msg_type="voice"
    )

    audio_out, path = await audio_service.synthesize(result["reply"])
    stored_path, _ = await storage_service.save_bytes(audio_out, "reply.mp3", "tts")

    return VoiceChatOut(
        session_id=result["session_id"],
        text=text,
        reply=result["reply"],
        audio_url=storage_service.presigned_url(stored_path),
        actions=result["actions"],
    )


__all__ = ["router", "ChatIn"]
