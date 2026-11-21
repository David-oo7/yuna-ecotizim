import io
import tempfile
from pathlib import Path

from app.services import docx_service


def _make_docx(paragraphs: list[str]) -> bytes:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "namuna.docx"
        docx_service.make_document(paragraphs, path)
        return path.read_bytes()


async def test_upload_and_edit_creates_version(client, user):
    content = _make_docx(["Shartnoma matni", "Ikkinchi paragraf", "Uchinchi paragraf"])
    upload = await client.post(
        "/api/v1/docs/upload",
        headers=user["headers"],
        files={
            "file": (
                "shartnoma.docx",
                io.BytesIO(content),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert upload.status_code == 201, upload.text
    original = upload.json()
    assert original["version"] == 1

    edited = await client.post(
        "/api/v1/docs/edit",
        headers=user["headers"],
        json={"file_id": original["file_id"], "instruction": "xatolarni tuzat"},
    )
    assert edited.status_code == 200, edited.text
    new_file = edited.json()
    assert new_file["version"] == 2
    assert new_file["file_id"] != original["file_id"]

    downloaded = await client.get(
        f"/api/v1/docs/{new_file['file_id']}/download", headers=user["headers"]
    )
    assert downloaded.status_code == 200

    from docx import Document

    document = Document(io.BytesIO(downloaded.content))
    texts = [p.text for p in document.paragraphs]
    assert texts[0].endswith("(tahrirlandi)")
    assert texts[1] == "Ikkinchi paragraf"  # tegilmagan

    # asl fayl saqlanib qolgan
    still_there = await client.get(
        f"/api/v1/docs/{original['file_id']}/download", headers=user["headers"]
    )
    assert still_there.status_code == 200


async def test_upload_rejects_non_docx(client, user):
    response = await client.post(
        "/api/v1/docs/upload",
        headers=user["headers"],
        files={"file": ("eski.doc", b"qandaydir matn", "application/msword")},
    )
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "UNSUPPORTED_TYPE"


async def test_foreign_doc_forbidden(client, user):
    import tests.conftest as conftest

    other = await conftest.make_user(client, "Begona")
    content = _make_docx(["Maxfiy hujjat"])
    upload = await client.post(
        "/api/v1/docs/upload",
        headers=user["headers"],
        files={"file": ("maxfiy.docx", io.BytesIO(content), "application/octet-stream")},
    )
    file_id = upload.json()["file_id"]

    response = await client.get(
        f"/api/v1/docs/{file_id}/download", headers=other["headers"]
    )
    assert response.status_code == 404
