"""Ma'lumotlar bazasi modellari (6-bo'limdagi sxemaning SQLAlchemy ko'rinishi).

Barcha vaqtlar UTC da saqlanadi; foydalanuvchiga ko'rsatishda vaqt zonasi qo'llanadi.
"""

from datetime import date, datetime, time, timezone

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    TypeDecorator,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# SQLite'da BIGSERIAL yo'q — Integer ishlatiladi (autoincrement uchun).
BigIntPK = BigInteger().with_variant(Integer, "sqlite")
# SQLite'da JSONB yo'q — JSON ishlatiladi.
JSONType = JSON().with_variant(JSONB, "postgresql")


class UTCDateTime(TypeDecorator):
    """Vaqtni har doim UTC da saqlaydi va UTC (aware) ko'rinishida qaytaradi.

    SQLite vaqt zonasini saqlamaydi — bu turdagi dekorator buni tekislaydi,
    shuning uchun kod PostgreSQL va SQLite'da bir xil ishlaydi.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str | None] = mapped_column(Text)
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Tashkent")
    language: Mapped[str] = mapped_column(String(8), default="uz")
    advice_time: Mapped[time] = mapped_column(Time, default=time(8, 0))
    kcal_goal: Mapped[int] = mapped_column(Integer, default=2200)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    devices: Mapped[list["Device"]] = relationship(back_populates="user")


class Device(Base):
    __tablename__ = "devices"
    __table_args__ = (UniqueConstraint("user_id", "device_uid", name="uq_device_user_uid"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    device_uid: Mapped[str] = mapped_column(String(64), nullable=False)
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    model: Mapped[str | None] = mapped_column(String(120))
    fcm_token: Mapped[str | None] = mapped_column(Text)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_seen_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    user: Mapped[User] = relationship(back_populates="devices")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    device_id: Mapped[int | None] = mapped_column(ForeignKey("devices.id", ondelete="SET NULL"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class ChatSession(Base):
    __tablename__ = "sessions"
    __table_args__ = (Index("ix_sessions_user_updated", "user_id", "updated_at"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200), default="Yangi suhbat")
    last_device_id: Mapped[int | None] = mapped_column(ForeignKey("devices.id", ondelete="SET NULL"))
    state_json: Mapped[dict] = mapped_column(JSONType, default=dict)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=utcnow, onupdate=utcnow
    )
    archived_at: Mapped[datetime | None] = mapped_column(UTCDateTime)


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_session_id", "session_id", "id"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    type: Mapped[str] = mapped_column(String(16), default="text")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[dict] = mapped_column(JSONType, default=dict)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class Reminder(Base):
    __tablename__ = "reminders"
    __table_args__ = (Index("ix_reminders_due", "remind_at", "status"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    remind_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    repeat_rule: Mapped[str | None] = mapped_column(String(16))
    channel: Mapped[str] = mapped_column(String(16), default="both")
    status: Mapped[str] = mapped_column(String(16), default="pending")
    last_sent_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class AdviceLog(Base):
    __tablename__ = "advice_log"
    __table_args__ = (UniqueConstraint("user_id", "log_date", name="uq_advice_user_date"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    channels: Mapped[list] = mapped_column(JSONType, default=list)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class FoodLog(Base):
    __tablename__ = "food_logs"
    __table_args__ = (Index("ix_food_user_date", "user_id", "eaten_at"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    eaten_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    meal_type: Mapped[str] = mapped_column(String(16), default="lunch")
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    amount_text: Mapped[str | None] = mapped_column(String(80))
    grams: Mapped[float | None] = mapped_column(Numeric(7, 1))
    kcal: Mapped[float] = mapped_column(Numeric(7, 1), default=0)
    protein: Mapped[float] = mapped_column(Numeric(7, 1), default=0)
    fat: Mapped[float] = mapped_column(Numeric(7, 1), default=0)
    carbs: Mapped[float] = mapped_column(Numeric(7, 1), default=0)
    source: Mapped[str] = mapped_column(String(16), default="text")
    confidence: Mapped[str] = mapped_column(String(16), default="medium")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class FileRecord(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("files.id", ondelete="SET NULL"))
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    mime: Mapped[str] = mapped_column(String(120), default="application/octet-stream")
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class DeviceCommand(Base):
    __tablename__ = "device_commands"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    target_device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), index=True
    )
    command: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONType, default=dict)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    result: Mapped[dict | None] = mapped_column(JSONType)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    delivered_at: Mapped[datetime | None] = mapped_column(UTCDateTime)


class InstalledApp(Base):
    __tablename__ = "installed_apps"
    __table_args__ = (UniqueConstraint("device_id", "package_name", name="uq_app_device_pkg"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"))
    app_name: Mapped[str] = mapped_column(String(200), nullable=False)
    package_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class TelegramChat(Base):
    __tablename__ = "telegram_chats"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    mode: Mapped[str] = mapped_column(String(16), default="manual")
    memory_summary: Mapped[str | None] = mapped_column(Text)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    last_message_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


__all__ = [
    "Base",
    "User",
    "Device",
    "RefreshToken",
    "ChatSession",
    "Message",
    "Reminder",
    "AdviceLog",
    "FoodLog",
    "FileRecord",
    "DeviceCommand",
    "InstalledApp",
    "TelegramChat",
    "utcnow",
    "JSONType",
    "UTCDateTime",
]
