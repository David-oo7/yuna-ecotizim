import io

# 1x1 o'lchamli eng kichik PNG
TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c6360000002000100ffff03000006000557bfabd400"
    "00000049454e44ae426082"
)


async def test_stt_and_tts(client, user):
    stt = await client.post(
        "/api/v1/voice/stt",
        headers=user["headers"],
        files={"audio": ("gap.m4a", io.BytesIO(b"fake-audio"), "audio/m4a")},
    )
    assert stt.status_code == 200
    assert stt.json()["text"]

    tts = await client.post(
        "/api/v1/voice/tts", headers=user["headers"], json={"text": "salom, men Yuna"}
    )
    assert tts.status_code == 200
    assert tts.json()["audio_url"].startswith("http")


async def test_voice_chat(client, user):
    response = await client.post(
        "/api/v1/voice/chat",
        headers=user["headers"],
        files={"audio": ("gap.m4a", io.BytesIO(b"fake-audio"), "audio/m4a")},
        data={"session_id": ""},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["text"] and body["reply"] and body["audio_url"]
    assert body["session_id"] > 0


async def test_vision_explain(client, user):
    response = await client.post(
        "/api/v1/vision/explain",
        headers=user["headers"],
        files={"image": ("rasm.png", io.BytesIO(TINY_PNG), "image/png")},
        data={"question": "Bu rasmda nima bor?"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["reply"]


async def test_device_register_sync_and_command(client, user):
    registered = await client.post(
        "/api/v1/devices/register",
        headers=user["headers"],
        json={"device_uid": "android-001", "type": "android", "model": "Pixel"},
    )
    assert registered.status_code == 200
    device_id = registered.json()["id"]

    synced = await client.post(
        "/api/v1/devices/apps/sync",
        headers=user["headers"],
        json={
            "device_uid": "android-001",
            "apps": [
                {"app_name": "Telegram", "package_name": "org.telegram.messenger"},
                {"app_name": "YouTube", "package_name": "com.google.android.youtube"},
            ],
        },
    )
    assert synced.status_code == 200
    assert synced.json()["synced"] == 2

    command = await client.post(
        "/api/v1/devices/command",
        headers=user["headers"],
        json={
            "target_device_id": device_id,
            "command": "open_app",
            "payload": {"package_name": "org.telegram.messenger"},
        },
    )
    assert command.status_code == 202
    command_id = command.json()["id"]

    ack = await client.post(
        f"/api/v1/devices/commands/{command_id}/ack",
        headers=user["headers"],
        json={"ok": True},
    )
    assert ack.status_code == 200
    assert ack.json()["status"] == "done"


async def test_open_app_intent_creates_command(client, user):
    await client.post(
        "/api/v1/devices/register",
        headers=user["headers"],
        json={"device_uid": "android-002", "type": "android"},
    )
    response = await client.post(
        "/api/v1/chat", headers=user["headers"], json={"text": "Telegramni och"}
    )
    assert response.status_code == 200
    actions = response.json()["actions"]
    assert actions and actions[0]["type"] == "app_open"
    assert actions[0]["payload"]["package_name"] == "org.telegram.messenger"


async def test_foreign_device_forbidden(client, user):
    import tests.conftest as conftest

    other = await conftest.make_user(client, "Begona")
    registered = await client.post(
        "/api/v1/devices/register",
        headers=user["headers"],
        json={"device_uid": "win-001", "type": "windows"},
    )
    device_id = registered.json()["id"]

    response = await client.post(
        "/api/v1/devices/command",
        headers=other["headers"],
        json={"target_device_id": device_id, "command": "ping", "payload": {}},
    )
    assert response.status_code == 404
