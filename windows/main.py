"""Y.U.N.A — Windows ilovasi (PySide6).

Ishga tushirish:
    pip install -r requirements.txt
    python main.py
"""

from __future__ import annotations

import asyncio
import html
import os
import sys

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QIcon, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from api import ApiError, YunaAPI

BASE_URL = os.getenv("YUNA_API_URL", "http://127.0.0.1:8000")
ACCENT = "#7C5CFF"


def resource_path(name: str) -> str:
    """Fayl yo'li: .exe ichida ham, oddiy ishga tushirishda ham ishlaydi."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


# ----------------------------- WebSocket -----------------------------
class WSThread(QThread):
    message = Signal(dict)

    def __init__(self, url: str) -> None:
        super().__init__()
        self.url = url
        self._stop = False

    def run(self) -> None:
        asyncio.run(self._loop())

    async def _loop(self) -> None:
        try:
            import websockets
        except ImportError:
            return
        while not self._stop:
            try:
                async with websockets.connect(self.url) as socket:
                    while not self._stop:
                        raw = await asyncio.wait_for(socket.recv(), timeout=30)
                        self.message.emit(__import__("json").loads(raw))
            except Exception:
                await asyncio.sleep(3)

    def stop(self) -> None:
        self._stop = True


# ----------------------------- Login -----------------------------
class LoginWindow(QWidget):
    success = Signal()

    def __init__(self, api: YunaAPI) -> None:
        super().__init__()
        self.api = api
        self.setWindowTitle("Yuna — kirish")
        self.setFixedSize(380, 320)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(10)

        title = QLabel("Y.U.N.A")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"font-size: 30px; font-weight: 700; color: {ACCENT};")
        layout.addWidget(title)

        subtitle = QLabel("Sizning shaxsiy yordamchingiz")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #777; margin-bottom: 12px;")
        layout.addWidget(subtitle)

        self.name = QLineEdit()
        self.name.setPlaceholderText("Ismingiz (yangi hisob uchun)")
        self.email = QLineEdit()
        self.email.setPlaceholderText("Email")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Parol")
        self.password.setEchoMode(QLineEdit.Password)
        for field in (self.name, self.email, self.password):
            layout.addWidget(field)

        mode_row = QHBoxLayout()
        self.mode = "login"
        self.toggle = QPushButton("Yangi hisob yaratish")
        self.toggle.setFlat(True)
        self.toggle.setStyleSheet(f"color: {ACCENT};")
        self.toggle.clicked.connect(self._toggle_mode)
        mode_row.addWidget(self.toggle)
        layout.addLayout(mode_row)

        self.submit = QPushButton("Kirish")
        self.submit.setStyleSheet(
            f"background: {ACCENT}; color: white; padding: 10px; border-radius: 8px; font-weight: 600;"
        )
        self.submit.clicked.connect(self._submit)
        layout.addWidget(self.submit)

        self.hint = QLabel("")
        self.hint.setWordWrap(True)
        self.hint.setStyleSheet("color: #c0392b;")
        layout.addWidget(self.hint)

        self.name.setVisible(False)
        self.password.returnPressed.connect(self._submit)

    def _toggle_mode(self) -> None:
        self.mode = "register" if self.mode == "login" else "login"
        is_register = self.mode == "register"
        self.name.setVisible(is_register)
        self.submit.setText("Ro'yxatdan o'tish" if is_register else "Kirish")
        self.toggle.setText("Hisobim bor" if is_register else "Yangi hisob yaratish")

    def _submit(self) -> None:
        self.hint.setText("")
        if not self.email.text().strip() or not self.password.text():
            self.hint.setText("Email va parolni kiriting.")
            return
        try:
            if self.mode == "register":
                if not self.name.text().strip():
                    self.hint.setText("Ismingizni kiriting.")
                    return
                self.api.register(self.name.text(), self.email.text(), self.password.text())
            else:
                self.api.login(self.email.text(), self.password.text())
        except ApiError as exc:
            self.hint.setText(str(exc))
            return
        self.api.register_device()
        self.success.emit()
        self.close()


# ----------------------------- Chat -----------------------------
class ChatWindow(QMainWindow):
    def __init__(self, api: YunaAPI) -> None:
        super().__init__()
        self.api = api
        self.session_id: int | None = None
        self.setWindowTitle("Y.U.N.A")
        self.resize(980, 680)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter()

        # chap panel
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(12, 12, 12, 12)
        brand = QLabel("Y.U.N.A")
        brand.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {ACCENT};")
        left_layout.addWidget(brand)
        self.new_button = QPushButton("+ Yangi suhbat")
        self.new_button.clicked.connect(self._new_session)
        left_layout.addWidget(self.new_button)
        self.session_list = QListWidget()
        self.session_list.itemClicked.connect(self._open_session)
        left_layout.addWidget(self.session_list)
        splitter.addWidget(left)

        # o'ng panel
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.view = QTextBrowser()
        self.view.setOpenExternalLinks(True)
        self.view.setStyleSheet("background: #fafafa; border: none; padding: 12px;")
        right_layout.addWidget(self.view)

        input_row = QWidget()
        input_layout = QHBoxLayout(input_row)
        input_layout.setContentsMargins(12, 8, 12, 12)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Yunaga yozing... (Enter — yuborish)")
        self.input.setStyleSheet("padding: 10px; border-radius: 8px; border: 1px solid #ddd;")
        self.input.returnPressed.connect(self._send)
        self.send_button = QPushButton("Yuborish")
        self.send_button.setStyleSheet(
            f"background: {ACCENT}; color: white; padding: 10px 18px; border-radius: 8px;"
        )
        self.send_button.clicked.connect(self._send)
        input_layout.addWidget(self.input)
        input_layout.addWidget(self.send_button)
        right_layout.addWidget(input_row)
        splitter.addWidget(right)
        splitter.setSizes([260, 720])
        layout.addWidget(splitter)

        self._bubbles: list[str] = []
        self._load_sessions()
        self._start_ws()

    # ---------- yordamchilar ----------
    def _render(self) -> None:
        self.view.setHtml(
            "<div style='font-family: Segoe UI, sans-serif; font-size: 14px;'>"
            + "".join(self._bubbles)
            + "</div>"
        )
        self.view.moveCursor(QTextCursor.End)

    def _bubble(self, role: str, text: str) -> str:
        safe = html.escape(text)
        # kod bloklarini monospace qilamiz
        parts = safe.split("```")
        formatted = ""
        for index, part in enumerate(parts):
            if index % 2 == 1:
                code = part.split("\n", 1)[-1] if "\n" in part else part
                formatted += (
                    "<pre style='background:#1e1e2e;color:#e6e6e6;padding:10px;"
                    "border-radius:8px;font-family:Consolas,monospace;white-space:pre-wrap;'>"
                    + code
                    + "</pre>"
                )
            else:
                formatted += part.replace("\n", "<br>")
        if role == "user":
            return (
                "<div style='text-align:right;margin:8px 0;'>"
                f"<span style='background:{ACCENT};color:white;padding:8px 12px;"
                "border-radius:12px;display:inline-block;max-width:70%;'>"
                f"{formatted}</span></div>"
            )
        return (
            "<div style='text-align:left;margin:8px 0;'>"
            "<span style='background:white;border:1px solid #eee;padding:8px 12px;"
            "border-radius:12px;display:inline-block;max-width:70%;'>"
            f"{formatted}</span></div>"
        )

    # ---------- amallar ----------
    def _load_sessions(self) -> None:
        self.session_list.clear()
        try:
            for item in self.api.sessions():
                row = QListWidgetItem(item["title"][:40])
                row.setData(Qt.UserRole, item["id"])
                self.session_list.addItem(row)
        except ApiError:
            pass

    def _new_session(self) -> None:
        self.session_id = None
        self._bubbles = []
        self._render()

    def _open_session(self, row) -> None:
        session_id = row.data(Qt.UserRole)
        try:
            detail = self.api.session(int(session_id))
        except ApiError as exc:
            QMessageBox.warning(self, "Xato", str(exc))
            return
        self.session_id = detail["id"]
        self._bubbles = []
        for message in detail["messages"]:
            self._bubbles.append(self._bubble(message["role"], message["content"]))
        self._render()

    def _send(self) -> None:
        text = self.input.text().strip()
        if not text:
            return
        self.input.clear()
        self._bubbles.append(self._bubble("user", text))
        self._render()
        self.send_button.setEnabled(False)
        QApplication.processEvents()

        try:
            data = self.api.chat(text, self.session_id)
            self.session_id = data["session_id"]
            self._bubbles.append(self._bubble("assistant", data["reply"]))
            if not self.session_list.count() or self.session_list.count() == 0:
                self._load_sessions()
        except ApiError as exc:
            self._bubbles.append(self._bubble("assistant", f"Xatolik: {exc}"))
        finally:
            self.send_button.setEnabled(True)
            self._render()

    def _start_ws(self) -> None:
        self.ws = WSThread(self.api.ws_url())
        self.ws.message.connect(self._on_ws)
        self.ws.start()

    def _on_ws(self, payload: dict) -> None:
        if payload.get("type") == "reminder":
            self._bubbles.append(self._bubble("assistant", f"⏰ {payload.get('text', '')}"))
            self._render()
        elif payload.get("type") == "advice":
            self._bubbles.append(self._bubble("assistant", f"🌸 {payload.get('text', '')}"))
            self._render()

    def closeEvent(self, event) -> None:  # noqa: N802
        try:
            self.ws.stop()
        except Exception:
            pass
        self.api.close()
        super().closeEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    icon = QIcon(resource_path("icon.png"))
    if not icon.isNull():
        app.setWindowIcon(icon)
    api = YunaAPI(BASE_URL)

    state: dict = {}

    def open_chat() -> None:
        window = ChatWindow(api)
        state["window"] = window  # havola saqlanadi, aks holda oyna yopiladi
        window._load_sessions()
        window.show()

    if api.restore_session():
        api.register_device()
        open_chat()
    else:
        login = LoginWindow(api)
        state["login"] = login
        login.success.connect(open_chat)
        login.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
