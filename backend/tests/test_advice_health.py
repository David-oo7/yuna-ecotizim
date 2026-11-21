async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["ai"] is True  # mock rejim yoqilgan


async def test_advice_is_idempotent(client, user):
    first = await client.get("/api/v1/advice/today", headers=user["headers"])
    assert first.status_code == 200
    second = await client.get("/api/v1/advice/today", headers=user["headers"])
    assert second.status_code == 200
    assert first.json()["text"] == second.json()["text"]
    assert first.json()["date"] == second.json()["date"]


async def test_telegram_webhook_secret(client):
    bad = await client.post("/api/v1/telegram/webhook/wrong", json={})
    assert bad.status_code == 403
    assert bad.json()["error"]["code"] == "FORBIDDEN"


async def test_error_envelope(client):
    response = await client.get("/api/v1/sessions/999")
    assert response.status_code == 401
    assert "error" in response.json()
