"""WebSocket ulanishlar reyestri: real vaqt sinxron va buyruq yetkazish."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WSManager:
    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(user_id, set()).add(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        bucket = self._connections.get(user_id)
        if bucket and websocket in bucket:
            bucket.discard(websocket)
            if not bucket:
                self._connections.pop(user_id, None)

    async def send_to_user(self, user_id: int, payload: dict[str, Any]) -> int:
        """Foydalanuvchining barcha ochiq qurilmalariga yuboradi. Nechta yetdi."""
        sent = 0
        for websocket in list(self._connections.get(user_id, set())):
            try:
                await websocket.send_json(payload)
                sent += 1
            except Exception:  # pragma: no cover
                self.disconnect(user_id, websocket)
        return sent

    def online(self, user_id: int) -> bool:
        return bool(self._connections.get(user_id))


manager = WSManager()
