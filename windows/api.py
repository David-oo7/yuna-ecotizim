"""Backend bilan aloqa: token saqlash, avtomatik yangilash."""

from __future__ import annotations

import json
import os
from pathlib import Path

import httpx

APP_NAME = "Yuna"
CONFIG_DIR = Path(os.getenv("APPDATA", Path.home())) / "Yuna"


def _secret_path() -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR / "session.json"


def save_tokens(tokens: dict) -> None:
    try:
        import keyring

        keyring.set_password(APP_NAME, "refresh_token", tokens["refresh_token"])
    except Exception:
        _secret_path().write_text(json.dumps({"refresh_token": tokens["refresh_token"]}))
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    (_secret_path().parent / "user.json").write_text(
        json.dumps(tokens["user"], ensure_ascii=False)
    )


def load_refresh_token() -> str | None:
    try:
        import keyring

        stored = keyring.get_password(APP_NAME, "refresh_token")
        if stored:
            return stored
    except Exception:
        pass
    if _secret_path().exists():
        try:
            return json.loads(_secret_path().read_text())["refresh_token"]
        except Exception:
            return None
    return None


def clear_tokens() -> None:
    try:
        import keyring

        keyring.delete_password(APP_NAME, "refresh_token")
    except Exception:
        pass
    try:
        _secret_path().unlink(missing_ok=True)
    except Exception:
        pass


class ApiError(Exception):
    def __init__(self, message: str, status: int = 0, code: str = "") -> None:
        super().__init__(message)
        self.status = status
        self.code = code


class YunaAPI:
    def __init__(self, base_url: str = "http://127.0.0.1:8000") -> None:
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(base_url=self.base_url, timeout=60)
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self.user: dict | None = None
        self.device_uid = "win-" + (CONFIG_DIR.name + str(os.getpid()))

    # ---------- pastdarajali ----------
    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}

    def _raise(self, response: httpx.Response) -> dict:
        try:
            payload = response.json()
        except Exception:
            raise ApiError(f"Server xatosi ({response.status_code})", response.status_code)
        error = payload.get("error") or {}
        raise ApiError(
            error.get("message") or "Xatolik yuz berdi",
            response.status_code,
            error.get("code", ""),
        )

    def _request(self, method: str, path: str, **kwargs) -> dict:
        response = self.client.request(method, path, headers=self._headers(), **kwargs)
        if response.status_code == 401 and self.refresh_token:
            if self.refresh():
                response = self.client.request(method, path, headers=self._headers(), **kwargs)
        if response.status_code >= 400:
            self._raise(response)
        if response.status_code == 204 or not response.content:
            return {}
        return response.json()

    # ---------- auth ----------
    def _store(self, data: dict) -> dict:
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        self.user = data["user"]
        save_tokens(data)
        return data

    def register(self, name: str, email: str, password: str) -> dict:
        data = self._request(
            "POST",
            "/api/v1/auth/register",
            json={"name": name, "email": email, "password": password},
        )
        return self._store(data)

    def login(self, email: str, password: str) -> dict:
        data = self._request(
            "POST", "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return self._store(data)

    def refresh(self) -> bool:
        if not self.refresh_token:
            return False
        try:
            response = self.client.post(
                "/api/v1/auth/refresh", json={"refresh_token": self.refresh_token}
            )
            if response.status_code != 200:
                return False
            self._store(response.json())
            return True
        except Exception:
            return False

    def restore_session(self) -> bool:
        self.refresh_token = load_refresh_token()
        return self.refresh()

    # ---------- ish ----------
    def chat(self, text: str, session_id: int | None = None) -> dict:
        return self._request(
            "POST",
            "/api/v1/chat",
            json={"text": text, "session_id": session_id},
        )

    def sessions(self) -> list[dict]:
        return self._request("GET", "/api/v1/sessions").get("items", [])

    def session(self, session_id: int) -> dict:
        return self._request("GET", f"/api/v1/sessions/{session_id}")

    def handoff(self, session_id: int) -> dict:
        return self._request("POST", f"/api/v1/sessions/{session_id}/handoff")

    def register_device(self) -> None:
        try:
            self._request(
                "POST",
                "/api/v1/devices/register",
                json={"device_uid": self.device_uid, "type": "windows", "model": "Windows"},
            )
        except ApiError:
            pass

    def ws_url(self) -> str:
        base = self.base_url.replace("https://", "wss://").replace("http://", "ws://")
        return f"{base}/ws?token={self.access_token}"

    def close(self) -> None:
        self.client.close()
