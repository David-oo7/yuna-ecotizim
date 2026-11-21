"""AI qaytargan `actions` ni haqiqiy amallarga aylantiradi.

Qoida: noto'g'ri yoki noma'lum action HECH QACHON taxmin bilan bajarilmaydi.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Device, DeviceCommand, InstalledApp, User
from app.services import food_service, push_service, reminder_service, ws_manager

logger = logging.getLogger(__name__)

ALLOWED = {"reminder_create", "reminder_cancel", "food_log", "app_open"}


async def _pick_target_device(
    db: AsyncSession, user: User, package_name: str | None = None
) -> tuple[Device | None, str | None]:
    """Ilova o'rnatilgan qurilmani topadi (avval android)."""
    devices = await reminder_service.user_devices(db, user.id)
    if not devices:
        return None, package_name
    devices.sort(key=lambda d: (d.type != "android", d.id))

    if package_name:
        result = await db.execute(
            select(InstalledApp).where(InstalledApp.package_name == package_name)
        )
        found = {row.device_id for row in result.scalars().all()}
        for device in devices:
            if device.id in found:
                return device, package_name
    return devices[0], package_name


async def apply_actions(
    db: AsyncSession, user: User, actions: list[dict[str, Any]] | None
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for action in (actions or [])[:3]:
        kind = str(action.get("type") or "")
        payload = action.get("payload") or {}
        if kind not in ALLOWED or not isinstance(payload, dict):
            logger.info("Noma'lum action o'tkazib yuborildi: %s", kind)
            continue

        if kind == "reminder_create":
            reminder = await reminder_service.create(
                db,
                user,
                text=str(payload.get("text") or "Eslatma"),
                when=payload.get("when"),
                repeat_rule=payload.get("repeat_rule"),
                channel=str(payload.get("channel") or "both"),
            )
            results.append(
                {
                    "type": "reminder_created",
                    "id": reminder.id,
                    "payload": {"remind_at": reminder.remind_at.isoformat()},
                }
            )

        elif kind == "reminder_cancel":
            reminder = await reminder_service.cancel_latest(db, user)
            results.append(
                {
                    "type": "reminder_cancelled",
                    "id": reminder.id if reminder else None,
                    "payload": {},
                }
            )

        elif kind == "food_log":
            items = payload.get("items") or []
            if isinstance(items, list) and items:
                logs = await food_service.add_items(db, user, items)
                results.append(
                    {
                        "type": "food_logged",
                        "id": logs[0].id if logs else None,
                        "payload": {"count": len(logs)},
                    }
                )

        elif kind == "app_open":
            app_name = str(payload.get("app_name") or "").strip()
            package = str(payload.get("package_name") or "").strip() or None
            if not package and app_name:
                result = await db.execute(
                    select(InstalledApp).where(
                        InstalledApp.app_name.ilike(f"%{app_name}%")
                    )
                )
                row = result.scalars().first()
                if row:
                    package = row.package_name

            device, package = await _pick_target_device(db, user, package)
            if device is None:
                results.append(
                    {
                        "type": "app_open_failed",
                        "id": None,
                        "payload": {"reason": "Qurilma topilmadi"},
                    }
                )
                continue

            command = DeviceCommand(
                user_id=user.id,
                target_device_id=device.id,
                command="open_app",
                payload={"app_name": app_name, "package_name": package},
                status="pending",
            )
            db.add(command)
            await db.flush()

            delivered = await ws_manager.manager.send_to_user(
                user.id,
                {
                    "type": "command",
                    "command": {
                        "id": command.id,
                        "command": "open_app",
                        "payload": command.payload,
                    },
                },
            )
            if delivered:
                command.status = "delivered"
            elif device.fcm_token:
                await push_service.send(
                    device.fcm_token,
                    "Yuna",
                    f"{app_name or 'Ilova'} ochilmoqda",
                    {"command": "open_app", "package": package or ""},
                )

            results.append(
                {
                    "type": "app_open",
                    "id": command.id,
                    "payload": {"device_id": device.id, "package_name": package},
                }
            )

    await db.flush()
    return results
