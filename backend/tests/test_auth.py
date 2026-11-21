from tests.conftest import make_user


async def test_register_login_refresh(client):
    user = await make_user(client)
    assert user["access_token"] and user["refresh_token"]
    assert user["user"]["name"] == "Doston"

    login = await client.post(
        "/api/v1/auth/login", json={"email": user["email"], "password": "parol123"}
    )
    assert login.status_code == 200
    tokens = login.json()

    refreshed = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refreshed.status_code == 200
    new_tokens = refreshed.json()
    assert new_tokens["access_token"] != tokens["access_token"]

    # rotatsiya: eski refresh endi ishlamaydi
    replay = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert replay.status_code == 401
    assert replay.json()["error"]["code"] == "AUTH_INVALID"


async def test_wrong_password(client):
    user = await make_user(client)
    response = await client.post(
        "/api/v1/auth/login", json={"email": user["email"], "password": "notogri"}
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_INVALID"


async def test_duplicate_email(client):
    user = await make_user(client)
    response = await client.post(
        "/api/v1/auth/register",
        json={"name": "Boshqa", "email": user["email"], "password": "parol123"},
    )
    assert response.status_code == 409


async def test_me_requires_token(client):
    assert (await client.get("/api/v1/me")).status_code == 401
    user = await make_user(client)
    me = await client.get("/api/v1/me", headers=user["headers"])
    assert me.status_code == 200
    assert me.json()["email"] == user["email"]


async def test_update_me(client):
    user = await make_user(client)
    response = await client.patch(
        "/api/v1/me", headers=user["headers"], json={"name": "Doston A.", "kcal_goal": 2400}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Doston A."
    assert response.json()["kcal_goal"] == 2400
