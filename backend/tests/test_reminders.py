from datetime import datetime, timedelta, timezone

from app.services.reminder_service import parse_when
from zoneinfo import ZoneInfo


async def test_reminder_created_from_chat(client, user):
    response = await client.post(
        "/api/v1/chat",
        headers=user["headers"],
        json={"text": "ertaga soat 9 da dori ichishni eslat"},
    )
    assert response.status_code == 200, response.text
    actions = response.json()["actions"]
    assert actions[0]["type"] == "reminder_created"

    reminders = await client.get("/api/v1/reminders", headers=user["headers"])
    items = reminders.json()["items"]
    assert len(items) == 1
    assert items[0]["status"] == "pending"

    remind_at = datetime.fromisoformat(items[0]["remind_at"])
    local = remind_at.astimezone(ZoneInfo("Asia/Tashkent"))
    assert local.hour == 9 and local.minute == 0


async def test_reminder_crud(client, user):
    created = await client.post(
        "/api/v1/reminders",
        headers=user["headers"],
        json={"text": "suv ichish", "when": "10 daqiqadan keyin", "repeat_rule": "daily"},
    )
    assert created.status_code == 201
    reminder = created.json()
    assert reminder["repeat_rule"] == "daily"

    updated = await client.patch(
        f"/api/v1/reminders/{reminder['id']}",
        headers=user["headers"],
        json={"text": "2 stakan suv"},
    )
    assert updated.status_code == 200
    assert updated.json()["text"] == "2 stakan suv"

    deleted = await client.delete(
        f"/api/v1/reminders/{reminder['id']}", headers=user["headers"]
    )
    assert deleted.status_code == 204

    pending = await client.get(
        "/api/v1/reminders?status=pending", headers=user["headers"]
    )
    assert pending.json()["items"] == []


async def test_due_reminder_delivery(session_factory, user, client):
    """Vaqti kelgan eslatma yuboriladi va takrorlanish uchun nusxa yaratiladi."""
    from app.scheduler.jobs import deliver_due_reminders

    past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    created = await client.post(
        "/api/v1/reminders",
        headers=user["headers"],
        json={"text": "dori", "remind_at": past, "repeat_rule": "daily"},
    )
    assert created.status_code == 201

    sent = await deliver_due_reminders(session_factory)
    assert sent == 1

    reminders = (await client.get("/api/v1/reminders", headers=user["headers"])).json()["items"]
    statuses = sorted(r["status"] for r in reminders)
    assert statuses == ["pending", "sent"]

    # ikkinchi marta chaqirilganda qayta yuborilmaydi
    assert await deliver_due_reminders(session_factory) == 0


def test_parse_when_variants():
    tz = ZoneInfo("Asia/Tashkent")
    now = datetime(2026, 11, 21, 10, 0, tzinfo=timezone.utc)

    assert parse_when("5 daqiqadan keyin", tz, now) == now + timedelta(minutes=5)
    assert parse_when("in 2 hours", tz, now) == now + timedelta(hours=2)

    tomorrow = parse_when("ertaga 09:00", tz, now).astimezone(tz)
    assert tomorrow.hour == 9
    assert tomorrow.date() > now.astimezone(tz).date()

    iso = parse_when("2026-12-01T12:30:00+05:00", tz, now)
    assert iso.astimezone(tz).hour == 12
