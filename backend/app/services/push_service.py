"""Push (FCM) — sozlanmagan bo'lsa jimgina `False` qaytaradi."""

from __future__ import annotations

import asyncio
import json
import logging

from app.config import settings

logger = logging.getLogger(__name__)


def _send_sync(token: str, title: str, body: str, data: dict[str, str]) -> bool:
    try:
        import firebase_admin
        from firebase_admin import credentials, messaging
    except ImportError:
        logger.info("firebase-admin o'rnatilmagan — push o'tkazib yuborildi")
        return False

    try:
        if not firebase_admin._apps:  # pragma: no cover - tashqi
            cred = credentials.Certificate(json.loads(settings.fcm_credentials_json))
            firebase_admin.initialize_app(cred)
        message = messaging.Message(
            token=token,
            notification=messaging.Notification(title=title, body=body),
            data=data,
        )
        messaging.send(message)
        return True
    except Exception as exc:  # pragma: no cover
        logger.warning("Push yuborilmadi: %s", exc)
        return False


async def send(token: str | None, title: str, body: str, data: dict[str, str] | None = None) -> bool:
    if not token or not settings.fcm_credentials_json:
        return False
    return await asyncio.to_thread(_send_sync, token, title, body, data or {})
