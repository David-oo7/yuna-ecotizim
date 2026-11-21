"""Qurilmalarni ro'yxatga olish, ilovalar sinxroni va buyruqlar."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import AppError, get_current_user
from app.models import Device, DeviceCommand, InstalledApp, User, utcnow
from app.schemas import AppsSyncIn, CommandIn, CommandOut, DeviceOut, DeviceRegisterIn
from app.services import push_service, ws_manager

router = APIRouter(tags=["devices"])


@router.get("/devices")
async def list_devices(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> dict:
    result = await db.execute(select(Device).where(Device.user_id == user.id))
    items = [DeviceOut.model_validate(d) for d in result.scalars().all()]
    return {"items": items, "next_cursor": None}


@router.post("/devices/register", response_model=DeviceOut)
async def register_device(
    payload: DeviceRegisterIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DeviceOut:
    result = await db.execute(
        select(Device).where(Device.user_id == user.id, Device.device_uid == payload.device_uid)
    )
    device = result.scalar_one_or_none()
    if device is None:
        device = Device(
            user_id=user.id,
            device_uid=payload.device_uid,
            type=payload.type,
            model=payload.model,
            fcm_token=payload.fcm_token,
        )
        db.add(device)
    else:
        device.type = payload.type
        device.model = payload.model or device.model
        if payload.fcm_token:
            device.fcm_token = payload.fcm_token
        device.last_seen_at = utcnow()

    await db.commit()
    await db.refresh(device)
    return DeviceOut.model_validate(device)


@router.post("/devices/apps/sync")
async def sync_apps(
    payload: AppsSyncIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(Device).where(Device.user_id == user.id, Device.device_uid == payload.device_uid)
    )
    device = result.scalar_one_or_none()
    if device is None:
        raise AppError(404, "NOT_FOUND", "Qurilma topilmadi. Avval ro'yxatdan o'tkazing.")

    existing = await db.execute(select(InstalledApp).where(InstalledApp.device_id == device.id))
    current = {row.package_name: row for row in existing.scalars().all()}

    for app in payload.apps[:500]:
        package = str(app.get("package_name") or "").strip()
        name = str(app.get("app_name") or package).strip()
        if not package:
            continue
        row = current.get(package)
        if row:
            row.app_name = name
            row.last_seen_at = utcnow()
        else:
            db.add(
                InstalledApp(
                    device_id=device.id,
                    app_name=name[:200],
                    package_name=package[:255],
                    is_system=bool(app.get("is_system")),
                )
            )
    await db.commit()
    return {"synced": len(payload.apps), "device_id": device.id}


@router.post("/devices/command", response_model=CommandOut, status_code=202)
async def send_command(
    payload: CommandIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommandOut:
    device = await db.get(Device, payload.target_device_id)
    if device is None or device.user_id != user.id:
        raise AppError(404, "NOT_FOUND", "Qurilma topilmadi.")

    command = DeviceCommand(
        user_id=user.id,
        target_device_id=device.id,
        command=payload.command,
        payload=payload.payload,
        status="pending",
    )
    db.add(command)
    await db.commit()
    await db.refresh(command)

    delivered = await ws_manager.manager.send_to_user(
        user.id,
        {
            "type": "command",
            "command": {
                "id": command.id,
                "command": command.command,
                "payload": command.payload,
            },
        },
    )
    if delivered:
        command.status = "delivered"
        await db.commit()
    elif device.fcm_token:
        await push_service.send(
            device.fcm_token,
            "Yuna",
            "Yangi buyruq",
            {"command": command.command, "payload": str(command.payload)},
        )

    return CommandOut.model_validate(command)


@router.post("/devices/commands/{command_id}/ack")
async def ack_command(
    command_id: int,
    payload: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    command = await db.get(DeviceCommand, command_id)
    if command is None or command.user_id != user.id:
        raise AppError(404, "NOT_FOUND", "Buyruq topilmadi.")
    command.status = "done" if payload.get("ok", True) else "failed"
    command.result = payload
    await db.commit()
    return {"ok": True, "status": command.status}
