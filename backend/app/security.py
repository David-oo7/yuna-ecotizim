"""Parol hashlash, JWT va token yordamchilari."""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.config import settings

_hasher = PasswordHasher()

ACCESS = "access"
REFRESH = "refresh"


class TokenError(Exception):
    """Token yaroqsiz yoki muddati tugagan."""


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def _encode(payload: dict[str, Any], ttl: timedelta) -> str:
    now = datetime.now(timezone.utc)
    body = {**payload, "iat": int(now.timestamp()), "exp": now + ttl, "jti": uuid.uuid4().hex}
    return jwt.encode(body, settings.app_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: int) -> str:
    return _encode(
        {"sub": str(user_id), "type": ACCESS},
        timedelta(minutes=settings.access_token_ttl_min),
    )


def create_refresh_token(user_id: int) -> tuple[str, str]:
    """(xom token, hash) qaytaradi — bazada faqat hash saqlanadi."""
    raw = _encode(
        {"sub": str(user_id), "type": REFRESH},
        timedelta(days=settings.refresh_token_ttl_days),
    )
    return raw, hash_token(raw)


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token, settings.app_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("TOKEN_EXPIRED") from exc
    except jwt.PyJWTError as exc:
        raise TokenError("TOKEN_INVALID") from exc

    if payload.get("type") != expected_type:
        raise TokenError("TOKEN_INVALID")
    return payload
