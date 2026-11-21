"""Fayl ombori: lokal disk (dev) yoki Cloudflare R2 (production)."""

from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


def _safe_name(original: str) -> str:
    suffix = Path(original).suffix.lower()[:10]
    return f"{uuid.uuid4().hex}{suffix}"


async def save_bytes(data: bytes, original_name: str, folder: str = "files") -> tuple[str, int]:
    """(storage_path, size) qaytaradi."""
    name = _safe_name(original_name)
    key = f"{folder}/{name}"

    if settings.storage_driver == "r2":
        await asyncio.to_thread(_r2_put, key, data)
        return key, len(data)

    base = Path(settings.storage_local_dir).resolve()
    target = base / key
    target.parent.mkdir(parents=True, exist_ok=True)
    await asyncio.to_thread(target.write_bytes, data)
    return key, len(data)


async def read_bytes(storage_path: str) -> bytes:
    if settings.storage_driver == "r2":
        return await asyncio.to_thread(_r2_get, storage_path)
    target = Path(settings.storage_local_dir).resolve() / storage_path
    return await asyncio.to_thread(target.read_bytes)


def local_path(storage_path: str) -> Path:
    if settings.storage_driver == "r2":
        raise RuntimeError("R2 rejimida lokal yo'l yo'q")
    return Path(settings.storage_local_dir).resolve() / storage_path


def _r2_client():  # pragma: no cover - tashqi xizmat
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="auto",
    )


def _r2_put(key: str, data: bytes) -> None:  # pragma: no cover
    _r2_client().put_object(Bucket=settings.r2_bucket, Key=key, Body=data)


def _r2_get(key: str) -> bytes:  # pragma: no cover
    obj = _r2_client().get_object(Bucket=settings.r2_bucket, Key=key)
    return obj["Body"].read()


def presigned_url(storage_path: str, expires: int = 900) -> str:
    """Yuklab olish uchun vaqtinchalik havola (R2) yoki lokal API havolasi."""
    if settings.storage_driver == "r2":  # pragma: no cover
        return _r2_client().generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.r2_bucket, "Key": storage_path},
            ExpiresIn=expires,
        )
    return f"{settings.app_base_url}/api/v1/docs/by-path/{storage_path}?expires={expires}"
