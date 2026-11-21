"""Jonli serverga qarshi uchdan-uchga tekshiruv.

Ishlatish:
    python -m uvicorn app.main:app --port 8000     # boshqa terminalda
    python scripts/smoke_test.py
"""

from __future__ import annotations

import io
import sys

import httpx

BASE = "http://127.0.0.1:8000"
ok_count = 0
fail_count = 0


def check(name: str, condition: bool, extra: str = "") -> None:
    global ok_count, fail_count
    if condition:
        ok_count += 1
        print(f"  [OK]   {name} {extra}")
    else:
        fail_count += 1
        print(f"  [XATO] {name} {extra}")


def main() -> int:
    client = httpx.Client(base_url=BASE, timeout=30)

    print("\n1) Health")
    health = client.get("/health").json()
    check("server tirik", health["ok"] is True, str(health))

    print("\n2) Ro'yxatdan o'tish va kirish")
    email = "smoke@example.com"
    register = client.post(
        "/api/v1/auth/register",
        json={"name": "Doston", "email": email, "password": "parol123"},
    )
    if register.status_code == 409:
        register = client.post(
            "/api/v1/auth/login", json={"email": email, "password": "parol123"}
        )
    check("token olindi", register.status_code in (200, 201), f"HTTP {register.status_code}")
    tokens = register.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    me = client.get("/api/v1/me", headers=headers)
    check("profil o'qildi", me.status_code == 200, me.json().get("name", ""))

    print("\n3) Suhbat")
    chat = client.post("/api/v1/chat", headers=headers, json={"text": "salom yuna"})
    check("javob keldi", chat.status_code == 200, chat.json().get("reply", "")[:60])
    session_id = chat.json().get("session_id")

    print("\n4) Eslatma (tabiiy til)")
    reminder_chat = client.post(
        "/api/v1/chat",
        headers=headers,
        json={"text": "ertaga soat 9 da dori ichishni eslat", "session_id": session_id},
    )
    actions = reminder_chat.json().get("actions", [])
    check(
        "eslatma yaratildi",
        bool(actions) and actions[0]["type"] == "reminder_created",
        actions[0]["payload"].get("remind_at", "") if actions else "",
    )

    reminders = client.get("/api/v1/reminders", headers=headers).json()["items"]
    check("bazada ko'rinadi", len(reminders) >= 1, f"{len(reminders)} ta")

    print("\n5) Ovqat hisobi")
    food = client.post(
        "/api/v1/food/log",
        headers=headers,
        json={"text": "tushlikda 1 kosa osh va 2 ta non yedim"},
    )
    items = food.json().get("items", [])
    check("taomlar ajratildi", len(items) == 2, ", ".join(i["name"] for i in items))

    summary = client.get("/api/v1/food/summary", headers=headers).json()
    check("kunlik jami hisoblandi", summary["totals"]["kcal"] > 0, f"{summary['totals']['kcal']} kkal")

    print("\n6) Kundalik maslahat")
    advice = client.get("/api/v1/advice/today", headers=headers)
    check("maslahat berildi", advice.status_code == 200, advice.json().get("text", "")[:60])

    print("\n7) Ovoz va rasm")
    stt = client.post(
        "/api/v1/voice/stt",
        headers=headers,
        files={"audio": ("gap.m4a", io.BytesIO(b"demo-audio"), "audio/m4a")},
    )
    check("STT matn qaytardi", stt.status_code == 200, stt.json().get("text", ""))

    tts = client.post("/api/v1/voice/tts", headers=headers, json={"text": "Salom, men Yuna"})
    check("TTS audio havolasi", tts.status_code == 200, tts.json().get("audio_url", "")[:50])

    from docx import Document

    document = Document()
    document.add_paragraph("Shartnoma matni")
    document.add_paragraph("Ikkinchi band")
    buffer = io.BytesIO()
    document.save(buffer)

    uploaded = client.post(
        "/api/v1/docs/upload",
        headers=headers,
        files={"file": ("demo.docx", buffer.getvalue(), "application/octet-stream")},
    )
    check("docx yuklandi", uploaded.status_code == 201, f"v{uploaded.json().get('version')}")

    edited = client.post(
        "/api/v1/docs/edit",
        headers=headers,
        json={"file_id": uploaded.json()["file_id"], "instruction": "xatolarni tuzat"},
    )
    check("docx tahrirlandi", edited.status_code == 200, f"v{edited.json().get('version')}")

    print("\n8) Qurilma va ilova ochish")
    device = client.post(
        "/api/v1/devices/register",
        headers=headers,
        json={"device_uid": "smoke-android", "type": "android", "model": "Demo"},
    )
    check("qurilma ro'yxatga olindi", device.status_code == 200, f"id={device.json().get('id')}")

    client.post(
        "/api/v1/devices/apps/sync",
        headers=headers,
        json={
            "device_uid": "smoke-android",
            "apps": [{"app_name": "Telegram", "package_name": "org.telegram.messenger"}],
        },
    )
    open_chat = client.post("/api/v1/chat", headers=headers, json={"text": "Telegramni och"})
    open_actions = open_chat.json().get("actions", [])
    check(
        "buyruq yaratildi",
        bool(open_actions) and open_actions[0]["type"] == "app_open",
        str(open_actions[0]["payload"]) if open_actions else "",
    )

    print("\n9) Xavfsizlik")
    anonymous = client.get("/api/v1/sessions")
    check("tokensiz kirish yopiq", anonymous.status_code == 401)
    foreign = client.get("/api/v1/sessions/99999", headers=headers)
    check("yo'q sessiya 404", foreign.status_code == 404)

    print(f"\nNatija: {ok_count} ta o'tdi, {fail_count} ta xato")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
