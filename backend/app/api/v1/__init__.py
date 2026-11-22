"""Barcha v1 routerlari."""

from fastapi import APIRouter

from app.api.v1 import (
    admin,
    advice,
    auth,
    chat,
    devices,
    docs,
    food,
    reminders,
    sessions,
    telegram,
    vision,
    voice,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(chat.router)
api_router.include_router(sessions.router)
api_router.include_router(vision.router)
api_router.include_router(voice.router)
api_router.include_router(docs.router)
api_router.include_router(reminders.router)
api_router.include_router(advice.router)
api_router.include_router(food.router)
api_router.include_router(devices.router)
api_router.include_router(telegram.router)
