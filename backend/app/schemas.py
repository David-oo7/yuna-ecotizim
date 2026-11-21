"""Umumiy so'rov/javob sxemalari (Pydantic v2)."""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# ---------------- Auth ----------------
class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6, max_length=128)
    device_uid: str | None = None


class LoginIn(BaseModel):
    email: str
    password: str
    device_uid: str | None = None


class RefreshIn(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserOut"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str | None = None
    timezone: str
    language: str
    advice_time: Any = None
    kcal_goal: int


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    timezone: str | None = None
    advice_time: Any = None
    kcal_goal: int | None = Field(default=None, ge=800, le=6000)


# ---------------- Chat ----------------
class ChatIn(BaseModel):
    session_id: int | None = None
    text: str = Field(min_length=1, max_length=8000)
    mode: Literal["auto", "code"] = "auto"


class ActionOut(BaseModel):
    type: str
    id: int | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class ChatOut(BaseModel):
    session_id: int
    message_id: int
    reply: str
    actions: list[ActionOut] = Field(default_factory=list)
    usage: dict[str, int] = Field(default_factory=dict)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    role: str
    type: str
    content: str
    meta: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    state_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class SessionDetail(SessionOut):
    messages: list[MessageOut] = Field(default_factory=list)


# ---------------- Reminders ----------------
class ReminderIn(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    when: str | None = None
    remind_at: datetime | None = None
    repeat_rule: Literal["daily", "weekly", "monthly"] | None = None
    channel: Literal["push", "telegram", "both"] = "both"


class ReminderUpdate(BaseModel):
    text: str | None = None
    remind_at: datetime | None = None
    repeat_rule: Literal["daily", "weekly", "monthly"] | None = None
    status: Literal["pending", "sent", "cancelled", "failed"] | None = None


class ReminderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    remind_at: datetime
    repeat_rule: str | None = None
    channel: str
    status: str


# ---------------- Food ----------------
class FoodLogIn(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    source: Literal["text", "voice", "photo"] = "text"


class FoodItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    meal_type: str
    amount_text: str | None = None
    kcal: float
    protein: float
    fat: float
    carbs: float


class FoodLogOut(BaseModel):
    reply: str
    items: list[FoodItemOut] = Field(default_factory=list)


class FoodSummary(BaseModel):
    date: date
    goal_kcal: int
    totals: dict[str, float]
    meals: list[dict[str, Any]]
    note: str = "Raqamlar taxminiy."


# ---------------- Devices ----------------
class DeviceRegisterIn(BaseModel):
    device_uid: str = Field(min_length=4, max_length=64)
    type: Literal["android", "windows", "telegram"]
    model: str | None = None
    fcm_token: str | None = None


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_uid: str
    type: str
    model: str | None = None
    push_enabled: bool


class AppsSyncIn(BaseModel):
    device_uid: str
    apps: list[dict[str, Any]]


class CommandIn(BaseModel):
    target_device_id: int
    command: Literal["open_app", "open_url", "notify", "ping"]
    payload: dict[str, Any] = Field(default_factory=dict)


class CommandOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    command: str
    payload: dict[str, Any]
    status: str


# ---------------- Docs ----------------
class DocEditIn(BaseModel):
    file_id: int
    instruction: str = Field(min_length=2, max_length=2000)


class DocOut(BaseModel):
    file_id: int
    version: int
    original_name: str
    size_bytes: int
    download_url: str


# ---------------- Advice ----------------
class AdviceOut(BaseModel):
    date: date
    text: str


# ---------------- Vision / Voice ----------------
class VisionOut(BaseModel):
    session_id: int
    reply: str


class SttOut(BaseModel):
    text: str


class TtsIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class TtsOut(BaseModel):
    audio_url: str


class VoiceChatOut(BaseModel):
    session_id: int
    text: str
    reply: str
    audio_url: str | None = None
    actions: list[ActionOut] = Field(default_factory=list)


class HealthOut(BaseModel):
    ok: bool
    db: bool
    ai: bool
    version: str


TokenPair.model_rebuild()
