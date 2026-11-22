"""Umumiy bog'liqliklar: autentifikatsiya, xatolar, rate limit."""

from typing import Any

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Device, User
from app.security import TokenError, decode_token

bearer_scheme = HTTPBearer(auto_error=False)


class AppError(HTTPException):
    """Yagona xato formati: {"error": {"code", "message", "field"}}."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        field: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            detail={"code": code, "message": message, "field": field},
            headers=headers,
        )


def auth_required() -> AppError:
    return AppError(
        status.HTTP_401_UNAUTHORIZED, "AUTH_REQUIRED", "Avval tizimga kiring."
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise auth_required()
    try:
        payload = decode_token(credentials.credentials, "access")
    except TokenError as exc:
        code = "TOKEN_EXPIRED" if str(exc) == "TOKEN_EXPIRED" else "TOKEN_INVALID"
        raise AppError(status.HTTP_401_UNAUTHORIZED, code, "Token yaroqsiz.") from exc

    user = await db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise auth_required()
    return user


async def get_device(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_device_uid: str | None = Header(default=None, alias="X-Device-Uid"),
) -> Device | None:
    """Ixtiyoriy qurilma konteksti (sessiyaning last_device_id si uchun)."""
    if not x_device_uid:
        return None
    from sqlalchemy import select

    result = await db.execute(
        select(Device).where(Device.user_id == user.id, Device.device_uid == x_device_uid)
    )
    return result.scalar_one_or_none()


async def get_current_admin(user: User = Depends(get_current_user)) -> User:
    """Faqat admin foydalanuvchi o'tadi."""
    if not user.is_admin:
        raise AppError(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "Bu amal faqat admin uchun.")
    return user


def error_body(code: str, message: str, field: str | None = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "field": field}}
