from tests.conftest import make_user


async def test_chat_creates_session(client, user):
    response = await client.post(
        "/api/v1/chat", headers=user["headers"], json={"text": "salom yuna"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["session_id"] > 0
    assert "Yuna" in data["reply"]
    assert data["usage"]["output_tokens"] > 0

    sessions = await client.get("/api/v1/sessions", headers=user["headers"])
    assert len(sessions.json()["items"]) == 1

    detail = await client.get(
        f"/api/v1/sessions/{data['session_id']}", headers=user["headers"]
    )
    assert detail.status_code == 200
    messages = detail.json()["messages"]
    assert [m["role"] for m in messages] == ["user", "assistant"]


async def test_chat_continues_session(client, user):
    first = (
        await client.post("/api/v1/chat", headers=user["headers"], json={"text": "salom"})
    ).json()
    second = await client.post(
        "/api/v1/chat",
        headers=user["headers"],
        json={"text": "yana salom", "session_id": first["session_id"]},
    )
    assert second.status_code == 200
    assert second.json()["session_id"] == first["session_id"]

    detail = await client.get(
        f"/api/v1/sessions/{first['session_id']}", headers=user["headers"]
    )
    assert len(detail.json()["messages"]) == 4


async def test_code_mode(client, user):
    response = await client.post(
        "/api/v1/chat",
        headers=user["headers"],
        json={"text": "faylni o'qiydigan kod yoz", "mode": "code"},
    )
    assert response.status_code == 200
    assert "```" in response.json()["reply"]


async def test_isolation_between_users(client):
    alice = await make_user(client, "Alisa")
    bob = await make_user(client, "Bob")

    created = (
        await client.post("/api/v1/chat", headers=alice["headers"], json={"text": "salom"})
    ).json()

    assert (
        await client.get(f"/api/v1/sessions/{created['session_id']}", headers=bob["headers"])
    ).status_code == 404

    attempt = await client.post(
        "/api/v1/chat",
        headers=bob["headers"],
        json={"text": "o'z sahifamga yozaman", "session_id": created["session_id"]},
    )
    assert attempt.status_code == 404

    bob_sessions = await client.get("/api/v1/sessions", headers=bob["headers"])
    assert bob_sessions.json()["items"] == []


async def test_rate_limit(client, user):
    for _ in range(10):
        ok = await client.post("/api/v1/chat", headers=user["headers"], json={"text": "salom"})
        assert ok.status_code == 200
    limited = await client.post("/api/v1/chat", headers=user["headers"], json={"text": "salom"})
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "RATE_LIMITED"
    assert limited.headers.get("retry-after") == "60"
