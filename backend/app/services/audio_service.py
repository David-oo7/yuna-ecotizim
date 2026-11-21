"""Ovoz: TTS (edge-tts) va STT (OpenRouter) — ikkalasi ham mock rejimni biladi."""

from __future__ import annotations

import asyncio
import hashlib
import logging


from app.config import settings
from app.services import ai_service, persona

logger = logging.getLogger(__name__)

_cache: dict[str, bytes] = {}


async def synthesize(text: str) -> tuple[bytes, str]:
    """(audio, storage_path) qaytaradi. Bir xil matn qayta sintez qilinmaydi."""
    key = hashlib.sha256(f"{persona.YUNA_VOICE}|{text}".encode()).hexdigest()[:32]
    path = f"tts/{key}.mp3"
    if key in _cache:
        return _cache[key], path

    if settings.ai_mock or not _edge_available():
        audio = b"ID3\x04\x00\x00\x00\x00\x00\x00mock-audio"
        _cache[key] = audio
        return audio, path

    import edge_tts

    communicate = edge_tts.Communicate(text, persona.YUNA_VOICE, rate="+8%")
    buffer = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buffer.extend(chunk["data"])
    audio = bytes(buffer)
    _cache[key] = audio
    return audio, path


async def transcribe(audio: bytes, mime: str = "audio/m4a") -> str:
    return await ai_service.transcribe(audio, mime)


def _edge_available() -> bool:
    try:
        import edge_tts  # noqa: F401

        return True
    except ImportError:
        return False


async def cleanup() -> None:  # pragma: no cover
    await asyncio.sleep(0)
