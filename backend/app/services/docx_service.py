"""Word (.docx) fayllarni o'qish, AI o'zgarishlarini qo'llash va versiyalash."""

from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def read_paragraphs(path: Path) -> list[str]:
    from docx import Document

    document = Document(str(path))
    return [p.text for p in document.paragraphs]


def _set_paragraph_text(paragraph, text: str) -> None:
    """Formatlashni saqlab matnni almashtiradi (birinchi run uslubida)."""
    if paragraph.runs:
        paragraph.runs[0].text = text
        for run in paragraph.runs[1:]:
            run.text = ""
    else:
        paragraph.add_run(text)


def _apply_sync(source: Path, target: Path, changes: list[dict[str, Any]]) -> None:
    from docx import Document

    document = Document(str(source))
    paragraphs = document.paragraphs

    for change in changes:
        target_ref = str(change.get("target") or "")
        match = re.fullmatch(r"p:(\d+)", target_ref)
        if not match:
            continue  # jadvallar keyingi bosqichda
        index = int(match.group(1))
        if index >= len(paragraphs):
            continue
        if change.get("delete"):
            element = paragraphs[index]._element
            element.getparent().remove(element)
            continue
        new_text = str(change.get("new_text") or "")
        _set_paragraph_text(paragraphs[index], new_text)

    document.save(str(target))


async def apply_changes(source: Path, target: Path, changes: list[dict[str, Any]]) -> None:
    await asyncio.to_thread(_apply_sync, source, target, changes)


def make_document(paragraphs: list[str], target: Path) -> None:
    """Testlar va namunalar uchun oddiy docx yaratadi."""
    from docx import Document

    document = Document()
    for text in paragraphs:
        document.add_paragraph(text)
    target.parent.mkdir(parents=True, exist_ok=True)
    document.save(str(target))
