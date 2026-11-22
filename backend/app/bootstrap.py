"""Ishga tushishdagi tayyorgarlik: sxema va admin akkaunt.

Dev rejimida `create_all` mavjud jadvalga ustun qo'shmaydi, shuning uchun
yetishmayotgan `users.is_admin` ustuni shu yerda qo'shiladi.
"""

from __future__ import annotations

import logging

from sqlalchemy import inspect, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import engine, SessionLocal
from app.models import User
from app.security import hash_password

logger = logging.getLogger("yuna.bootstrap")


async def ensure_schema() -> None:
    """Eski bazalarga `is_admin` ustunini qo'shadi."""
    async with engine.begin() as conn:
        columns = await conn.run_sync(
            lambda sync_conn: [c["name"] for c in inspect(sync_conn).get_columns("users")]
        )
        if "is_admin" not in columns:
            await conn.execute(
                text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT false")
            )
            logger.info("users.is_admin ustuni qo'shildi")


async def ensure_admin_account() -> None:
    """Admin akkauntni yaratadi yoki mavjudini admin qilib belgilaydi."""
    email = (settings.admin_email or "").strip().lower()
    if not email or not settings.admin_password:
        logger.warning("ADMIN_EMAIL/ADMIN_PASSWORD yo'q — admin akkaunt yaratilmadi")
        return

    async with SessionLocal() as db:  # type: AsyncSession
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                name=settings.admin_name,
                email=email,
                password_hash=hash_password(settings.admin_password),
                is_admin=True,
                language="uz",
            )
            db.add(user)
            logger.info("Admin akkaunt yaratildi: %s", email)
        elif not user.is_admin:
            user.is_admin = True
            logger.info("Mavjud foydalanuvchi admin qilindi: %s", email)
        else:
            return
        await db.commit()


__all__ = ["ensure_schema", "ensure_admin_account"]
