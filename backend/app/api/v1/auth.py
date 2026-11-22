"""Ro'yxatdan o'tish, kirish, token yangilash."""

from datetime import datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.deps import AppError, get_current_user
from app.models import RefreshToken, User
from app.schemas import (
    LoginIn,
    PasswordChangeIn,
    RefreshIn,
    RegisterIn,
    TokenPair,
    UserOut,
    UserUpdate,
)
from app.security import (
    ACCESS,
    REFRESH,
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)

router = APIRouter(tags=["auth"])


def _parse_time(value: object) -> time | None:
    """"08:00", "08:00:00" yoki time obyektini qabul qiladi."""
    if isinstance(value, time):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(value.strip(), fmt).time()
        except ValueError:
            continue
    return None


async def issue_tokens(db: AsyncSession, user: User) -> TokenPair:
    access = create_access_token(user.id)
    refresh_raw, refresh_hash = create_refresh_token(user.id)
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.refresh_token_ttl_days),
        )
    )
    await db.commit()
    return TokenPair(
        access_token=access,
        refresh_token=refresh_raw,
        expires_in=settings.access_token_ttl_min * 60,
        user=UserOut.model_validate(user),
    )


@router.post("/auth/register", response_model=TokenPair, status_code=201)
async def register(payload: RegisterIn, db: AsyncSession = Depends(get_db)) -> TokenPair:
    email = payload.email.strip().lower()
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise AppError(409, "VALIDATION", "Bu email allaqachon ro'yxatdan o'tgan.", "email")

    user = User(name=payload.name.strip(), email=email, password_hash=hash_password(payload.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return await issue_tokens(db, user)


@router.post("/auth/login", response_model=TokenPair)
async def login(payload: LoginIn, db: AsyncSession = Depends(get_db)) -> TokenPair:
    email = payload.email.strip().lower()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not user.password_hash or not verify_password(
        user.password_hash, payload.password
    ):
        raise AppError(401, "AUTH_INVALID", "Email yoki parol xato.")
    return await issue_tokens(db, user)


@router.post("/auth/refresh", response_model=TokenPair)
async def refresh(payload: RefreshIn, db: AsyncSession = Depends(get_db)) -> TokenPair:
    try:
        decoded = decode_token(payload.refresh_token, REFRESH)
    except TokenError as exc:
        raise AppError(401, "AUTH_INVALID", "Refresh token yaroqsiz.") from exc

    token_hash = hash_token(payload.refresh_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    stored = result.scalar_one_or_none()
    if stored is None or stored.revoked_at is not None:
        raise AppError(401, "AUTH_INVALID", "Refresh token bekor qilingan.")

    user = await db.get(User, int(decoded["sub"]))
    if user is None:
        raise AppError(401, "AUTH_INVALID", "Foydalanuvchi topilmadi.")

    stored.revoked_at = datetime.now(timezone.utc)  # rotatsiya
    return await issue_tokens(db, user)


@router.post("/auth/logout", status_code=204)
async def logout(
    payload: RefreshIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(payload.refresh_token))
    )
    stored = result.scalar_one_or_none()
    if stored and stored.user_id == user.id:
        stored.revoked_at = datetime.now(timezone.utc)
        await db.commit()


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)


@router.patch("/me", response_model=UserOut)
async def update_me(
    payload: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    data = payload.model_dump(exclude_unset=True)

    email = data.pop("email", None)
    if email is not None:
        email = email.strip().lower()
        if email != (user.email or ""):
            taken = await db.execute(select(User).where(User.email == email, User.id != user.id))
            if taken.scalar_one_or_none():
                raise AppError(409, "VALIDATION", "Bu email band.", "email")
            user.email = email

    raw_time = data.pop("advice_time", None)
    if raw_time is not None:
        user.advice_time = _parse_time(raw_time)

    for field, value in data.items():
        if value is not None:
            setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)


@router.post("/auth/change-password", status_code=204)
async def change_password(
    payload: PasswordChangeIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    if user.password_hash and not verify_password(user.password_hash, payload.current_password):
        raise AppError(401, "AUTH_INVALID", "Joriy parol xato.", "current_password")
    user.password_hash = hash_password(payload.new_password)
    await db.commit()


__all__ = ["router", "issue_tokens", "ACCESS"]
