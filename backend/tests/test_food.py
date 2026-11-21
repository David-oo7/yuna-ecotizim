async def test_food_log_from_text(client, user):
    response = await client.post(
        "/api/v1/food/log",
        headers=user["headers"],
        json={"text": "tushlikda 1 kosa osh va 2 ta non yedim"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    names = sorted(item["name"] for item in data["items"])
    assert names == ["non", "osh"]
    assert "taxminiy" in data["reply"].lower()

    summary = await client.get("/api/v1/food/summary", headers=user["headers"])
    assert summary.status_code == 200
    body = summary.json()
    assert body["totals"]["kcal"] > 600
    assert body["goal_kcal"] == 2200
    assert body["note"] == "Raqamlar taxminiy."


async def test_food_delete(client, user):
    logged = (
        await client.post(
            "/api/v1/food/log", headers=user["headers"], json={"text": "1 ta olma yedim"}
        )
    ).json()
    log_id = logged["items"][0]["id"]

    assert (
        await client.delete(f"/api/v1/food/logs/{log_id}", headers=user["headers"])
    ).status_code == 204

    summary = (await client.get("/api/v1/food/summary", headers=user["headers"])).json()
    assert summary["totals"]["kcal"] == 0


async def test_food_summary_for_date(client, user):
    response = await client.get(
        "/api/v1/food/summary?date=2026-01-01", headers=user["headers"]
    )
    assert response.status_code == 200
    assert response.json()["date"] == "2026-01-01"
    assert response.json()["totals"]["kcal"] == 0
