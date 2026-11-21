"""Word (.docx) yuklash, AI bilan tahrirlash va versiyalash."""

import asyncio
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.deps import AppError, get_current_user
from app.models import FileRecord, User
from app.ratelimit import ai_limit
from app.schemas import DocEditIn, DocOut
from app.services import ai_service, docx_service, storage_service

router = APIRouter(tags=["docs"])

MAX_BYTES = settings.upload_max_mb * 1024 * 1024


def _doc_out(record: FileRecord) -> DocOut:
    return DocOut(
        file_id=record.id,
        version=record.version,
        original_name=record.original_name,
        size_bytes=record.size_bytes,
        download_url=storage_service.presigned_url(record.storage_path),
    )


@router.post("/docs/upload", response_model=DocOut, status_code=201)
async def upload(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocOut:
    name = file.filename or "hujjat.docx"
    if not name.lower().endswith(".docx"):
        raise AppError(415, "UNSUPPORTED_TYPE", "Faqat .docx fayl qabul qilinadi.")

    data = await file.read()
    if len(data) > MAX_BYTES:
        raise AppError(413, "FILE_TOO_LARGE", f"Fayl {settings.upload_max_mb} MB dan katta.")
    if not data:
        raise AppError(422, "VALIDATION", "Fayl bo'sh.", "file")

    path, size = await storage_service.save_bytes(data, name, "docs")
    record = FileRecord(
        user_id=user.id,
        kind="docx",
        original_name=name,
        storage_path=path,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        size_bytes=size,
        version=1,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return _doc_out(record)


@router.post("/docs/edit", response_model=DocOut)
async def edit(
    payload: DocEditIn,
    user: User = Depends(ai_limit),
    db: AsyncSession = Depends(get_db),
) -> DocOut:
    record = await db.get(FileRecord, payload.file_id)
    if record is None or record.user_id != user.id:
        raise AppError(404, "NOT_FOUND", "Fayl topilmadi.")

    source_bytes = await storage_service.read_bytes(record.storage_path)

    with tempfile.TemporaryDirectory() as tmp:
        source_path = Path(tmp) / "source.docx"
        target_path = Path(tmp) / "edited.docx"
        source_path.write_bytes(source_bytes)

        paragraphs = await asyncio.to_thread(docx_service.read_paragraphs, source_path)
        if not paragraphs:
            raise AppError(422, "VALIDATION", "Hujjat bo'sh ko'rinadi.", "file")

        try:
            result = await ai_service.docx_changes(paragraphs, payload.instruction)
        except ai_service.AIUnavailable as exc:
            raise AppError(503, "AI_UNAVAILABLE", str(exc)) from exc

        changes = result.get("changes") or []
        await docx_service.apply_changes(source_path, target_path, changes)
        new_bytes = target_path.read_bytes()

    path, size = await storage_service.save_bytes(new_bytes, record.original_name, "docs")
    new_record = FileRecord(
        user_id=user.id,
        parent_id=record.id,
        kind="docx",
        original_name=record.original_name,
        storage_path=path,
        mime=record.mime,
        size_bytes=size,
        version=record.version + 1,
    )
    db.add(new_record)
    await db.commit()
    await db.refresh(new_record)

    # Sessiya holatiga ochiq faylni yozamiz (qurilmalar orasida davom ettirish)
    from app.services import ws_manager

    await ws_manager.manager.send_to_user(
        user.id,
        {
            "type": "doc_ready",
            "file_id": new_record.id,
            "version": new_record.version,
            "parent_id": record.id,
        },
    )
    return _doc_out(new_record)


@router.get("/docs/{file_id}/download")
async def download(
    file_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await db.get(FileRecord, file_id)
    if record is None or record.user_id != user.id:
        raise AppError(404, "NOT_FOUND", "Fayl topilmadi.")

    if settings.storage_driver == "r2":
        return RedirectResponse(storage_service.presigned_url(record.storage_path))

    path = storage_service.local_path(record.storage_path)
    if not path.exists():
        raise AppError(404, "NOT_FOUND", "Fayl omborda topilmadi.")
    return FileResponse(
        path,
        media_type=record.mime,
        filename=record.original_name,
    )


@router.get("/docs/by-path/{storage_path:path}")
async def download_by_path(storage_path: str):
    """Vaqtinchalik havola (uuid nom) orqali yuklab olish."""
    if settings.storage_driver == "r2":
        return RedirectResponse(storage_service.presigned_url(storage_path))

    base = Path(settings.storage_local_dir).resolve()
    target = (base / storage_path).resolve()
    if base not in target.parents or not target.exists():
        raise AppError(404, "NOT_FOUND", "Fayl topilmadi.")
    return FileResponse(target, media_type="application/octet-stream", filename=target.name)
