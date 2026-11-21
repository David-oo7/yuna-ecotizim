"""Test muhiti: SQLite (StaticPool, xotirada), AI mock, alohida storage papka."""

import os
import sys
import tempfile
from pathlib import Path

# Ilova import qilinishidan OLDIN muhit o'zgaruvchilari
os.environ["APP_ENV"] = "test"
os.environ["AI_MOCK"] = "true"
os.environ["AUTO_MIGRATE"] = "false"
os.environ["STORAGE_DRIVER"] = "local"
os.environ["STORAGE_LOCAL_DIR"] = tempfile.mkdtemp(prefix="yuna-test-")
os.environ["APP_BASE_URL"] = "http://test"
os.environ["TELEGRAM_WEBHOOK_SECRET"] = "testsecret"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_yuna.db"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.db import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402
from app.ratelimit import reset as reset_rate_limit  # noqa: E402

test_engine = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest.fixture
async def session_factory():
    return TestSession


@pytest.fixture
async def client():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    reset_rate_limit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http

    app.dependency_overrides.clear()
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


_counter = {"n": 0}


async def make_user(client: AsyncClient, name: str = "Doston") -> dict:
    _counter["n"] += 1
    email = f"{name.lower()}{_counter['n']}@example.com"
    response = await client.post(
        "/api/v1/auth/register",
        json={"name": name, "email": email, "password": "parol123"},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    data["email"] = email
    data["headers"] = {"Authorization": f"Bearer {data['access_token']}"}
    return data


@pytest.fixture
async def user(client):
    return await make_user(client)
