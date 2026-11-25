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


def _config_path() -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR / "config.json"


def _read_json(path: Path):
    """BOM (utf-8-sig) bilan saqlangan fayllarni ham o'qiy oladi."""
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_config() -> dict:
    try:
        return _read_json(_config_path())
    except Exception:
        return {}


def save_config(data: dict) -> None:
    try:
        _config_path().write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )
    except Exception:
        pass


def save_tokens(tokens: dict) -> None:
    try:
        import keyring

        keyring.set_password(APP_NAME, "refresh_token", tokens["refresh_token"])
    except Exception:
        _secret_path().write_text(
            json.dumps({"refresh_token": tokens["refresh_token"]}), encoding="utf-8"
        )
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    (_secret_path().parent / "user.json").write_text(
        json.dumps(tokens["user"], ensure_ascii=False), encoding="utf-8"
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
            return _read_json(_secret_path())["refresh_token"]
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
        self.base_url = (load_config().get("api_url") or base_url).rstrip("/")
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

    # ---------- sozlamalar ----------
    def set_base_url(self, url: str) -> None:
        url = url.strip().rstrip("/")
        if not url:
            return
        config = load_config()
        config["api_url"] = url
        save_config(config)
        self.base_url = url
        self.client = httpx.Client(base_url=url, timeout=60)

    def me(self) -> dict:
        data = self._request("GET", "/api/v1/me")
        self.user = data
        return data

    def update_me(self, fields: dict) -> dict:
        data = self._request("PATCH", "/api/v1/me", json=fields)
        self.user = data
        return data

    def change_password(self, current: str, new: str) -> None:
        self._request(
            "POST",
            "/api/v1/auth/change-password",
            json={"current_password": current, "new_password": new},
        )

    def forget_session(self) -> None:
        clear_tokens()
        self.access_token = None
        self.refresh_token = None

    # ---------- eslatmalar ----------
    def reminders(self) -> list[dict]:
        return self._request("GET", "/api/v1/reminders").get("items", [])

    def create_reminder(self, text: str, remind_at: str) -> dict:
        return self._request(
            "POST",
            "/api/v1/reminders",
            json={"text": text, "remind_at": remind_at, "channel": "both"},
        )

    def delete_reminder(self, reminder_id: int) -> None:
        self._request("DELETE", f"/api/v1/reminders/{reminder_id}")

    # ---------- ovqat ----------
    def food_summary(self) -> dict:
        return self._request("GET", "/api/v1/food/summary")

    def log_food(self, text: str) -> dict:
        return self._request("POST", "/api/v1/food/log", json={"text": text})

    # ---------- hujjatlar ----------
    def documents(self) -> list[dict]:
        return self._request("GET", "/api/v1/docs").get("items", [])

    def upload_document(self, path: str) -> dict:
        with open(path, "rb") as handle:
            data = handle.read()
        return self._request(
            "POST",
            "/api/v1/docs/upload",
            files={
                "file": (
                    os.path.basename(path),
                    data,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
            timeout=300,
        )

    def edit_document(self, file_id: int, instruction: str) -> dict:
        return self._request(
            "POST",
            "/api/v1/docs/edit",
            json={"file_id": file_id, "instruction": instruction},
            timeout=300,
        )

    def download_document(self, file_id: int, target: str) -> None:
        response = self.client.get(
            f"/api/v1/docs/{file_id}/download",
            headers=self._headers(),
            follow_redirects=True,
            timeout=300,
        )
        if response.status_code >= 400:
            self._raise(response)
        Path(target).write_bytes(response.content)

    # ---------- umumiy fayllar ----------
    def files(self, kind: str | None = None) -> list[dict]:
        params = {"kind": kind} if kind else {}
        return self._request("GET", "/api/v1/files", params=params).get("items", [])

    def upload_file(self, path: str, kind: str = "laptop_file") -> dict:
        filename = os.path.basename(path)
        with open(path, "rb") as handle:
            data = handle.read()
        return self._request(
            "POST",
            "/api/v1/files/upload",
            data={"kind": kind},
            files={"file": (filename, data, "application/octet-stream")},
            timeout=300,
        )

    def delete_file(self, file_id: int) -> dict:
        return self._request("DELETE", f"/api/v1/files/{file_id}")

    def download_file(self, file_id: int, target: str) -> None:
        response = self.client.get(
            f"/api/v1/files/{file_id}/download",
            headers=self._headers(),
            follow_redirects=True,
            timeout=300,
        )
        if response.status_code >= 400:
            self._raise(response)
        Path(target).write_bytes(response.content)

    # ---------- vision / rasm tahlili ----------
    def explain_vision(self, image_path: str, question: str = "") -> dict:
        filename = os.path.basename(image_path)
        with open(image_path, "rb") as handle:
            data = handle.read()
        return self._request(
            "POST",
            "/api/v1/vision/explain",
            data={"question": question} if question else {},
            files={"image": (filename, data, "image/jpeg")},
            timeout=120,
        )

    # ---------- qurilma buyrug'i javobi ----------
    def ack_command(self, command_id: int, ok: bool = True, result: dict | None = None) -> dict:
        return self._request(
            "POST",
            f"/api/v1/devices/commands/{command_id}/ack",
            json={"ok": ok, **(result or {})},
        )

    # ---------- maslahat ----------
    def advice_today(self) -> dict:
        return self._request("GET", "/api/v1/advice/today")

    # ---------- admin ----------
    def admin_users(self) -> list[dict]:
        return self._request("GET", "/api/v1/admin/users").get("items", [])

    def admin_stats(self) -> dict:
        return self._request("GET", "/api/v1/admin/stats")

    def close(self) -> None:
        self.client.close()
