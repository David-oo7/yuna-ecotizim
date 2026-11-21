"""Baza ulanishi va sessiya bog'liqligi."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models import Base

connect_args = {}
if settings.database_url.startswith("sqlite"):
    # Bir jarayonda bir nechta async ulanish uchun
    connect_args = {"check_same_thread": False}

engine = create_async_engine(
    settings.database_url, echo=False, future=True, connect_args=connect_args
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


async def init_models() -> None:
    """Jadvallarni yaratadi (dev/test uchun; productionda Alembic ishlatiladi)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
