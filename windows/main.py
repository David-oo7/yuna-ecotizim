"""Y.U.N.A — Windows ilovasi (PySide6).

Bo'limlar: Suhbat, Eslatmalar, Ovqat, Maslahat, Sozlamalar (+ Admin).

Ishga tushirish:
    pip install -r requirements.txt
    python main.py
"""

from __future__ import annotations

import asyncio
import html
import json
import os
import sys
from datetime import datetime

from PySide6.QtCore import QDateTime, Qt, QThread, QTime, Signal
from PySide6.QtGui import QFont, QIcon, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QDateTimeEdit,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from api import ApiError, YunaAPI

BASE_URL = os.getenv("YUNA_API_URL", "http://127.0.0.1:8000")
ACCENT = "#7C5CFF"
ACCENT_SOFT = "#EDE9FF"
BG = "#F5F4FB"
MUTED = "#6B6B80"

MEAL_LABELS = {
    "breakfast": "Nonushta",
    "lunch": "Tushlik",
    "dinner": "Kechki ovqat",
    "snack": "Gazak",
}
LANGUAGES = {"uz": "O'zbekcha", "ru": "Русский", "en": "English"}
TIMEZONES = ["Asia/Tashkent", "Asia/Samarkand", "Asia/Almaty", "Europe/Moscow", "UTC"]

QSS = f"""
QWidget {{ background: {BG}; color: #1A1A1A; font-family: "Segoe UI", sans-serif; }}
QLabel, QCheckBox {{ background: transparent; }}
QFrame#sidebar {{ background: white; border: none; }}
QFrame#card {{ background: white; border: 1px solid #ECEBF5; border-radius: 14px; }}
QLabel#cardTitle {{ font-size: 15px; font-weight: 600; color: #1A1A1A; }}
QLabel#brand {{ font-size: 20px; font-weight: 700; color: {ACCENT}; }}
QLabel#muted {{ color: {MUTED}; }}
QLabel#big {{ font-size: 26px; font-weight: 700; color: {ACCENT}; }}
QPushButton#nav {{
    text-align: left; padding: 10px 14px; border: none; border-radius: 10px;
    background: transparent; color: #444; font-size: 14px;
}}
QPushButton#nav:hover {{ background: {ACCENT_SOFT}; }}
QPushButton#nav:checked {{ background: {ACCENT_SOFT}; color: {ACCENT}; font-weight: 600; }}
QPushButton {{
    padding: 9px 16px; border-radius: 9px; border: 1px solid #DEDCEA;
    background: white; color: #333;
}}
QPushButton:hover {{ border-color: {ACCENT}; }}
QPushButton#primary {{
    background: {ACCENT}; color: white; border: none; font-weight: 600;
}}
QPushButton#primary:hover {{ background: #6B4BE8; }}
QPushButton#danger {{ color: #C0392B; border-color: #F2C9C4; }}
QLineEdit, QComboBox, QSpinBox, QTimeEdit, QDateTimeEdit {{
    background: white; border: 1px solid #DEDCEA; border-radius: 9px;
    padding: 8px 10px; min-height: 20px;
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{ border-color: {ACCENT}; }}
QListWidget, QTableWidget, QTextBrowser {{
    background: white; border: 1px solid #ECEBF5; border-radius: 12px;
}}
QListWidget::item {{ padding: 8px; border-radius: 8px; }}
QListWidget::item:selected {{ background: {ACCENT_SOFT}; color: {ACCENT}; }}
QHeaderView::section {{
    background: #FAFAFE; border: none; border-bottom: 1px solid #ECEBF5;
    padding: 8px; color: {MUTED};
}}
"""


def resource_path(name: str) -> str:
    """Fayl yo'li: .exe ichida ham, oddiy ishga tushirishda ham ishlaydi."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def card_box(title: str = "") -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(18, 16, 18, 18)
    layout.setSpacing(10)
    if title:
        label = QLabel(title)
        label.setObjectName("cardTitle")
        layout.addWidget(label)
    return frame, layout


def to_local_text(value: str) -> str:
    """ISO vaqtni mahalliy ko'rinishga o'giradi."""
    try:
        moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return moment.astimezone().strftime("%d.%m.%Y %H:%M")
    except Exception:
        return str(value)


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
                        self.message.emit(json.loads(raw))
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
        self.setFixedSize(400, 340)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(10)

        title = QLabel("Y.U.N.A")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"font-size: 30px; font-weight: 700; color: {ACCENT};")
        layout.addWidget(title)

        subtitle = QLabel("Sizning shaxsiy yordamchingiz")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"color: {MUTED}; margin-bottom: 12px;")
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
        self.toggle.setStyleSheet(f"color: {ACCENT}; border: none;")
        self.toggle.clicked.connect(self._toggle_mode)
        mode_row.addWidget(self.toggle)
        layout.addLayout(mode_row)

        self.submit = QPushButton("Kirish")
        self.submit.setObjectName("primary")
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


# ----------------------------- Suhbat -----------------------------
class ChatPage(QWidget):
    def __init__(self, api: YunaAPI, parent=None) -> None:
        super().__init__(parent)
        self.api = api
        self.session_id: int | None = None
        self._bubbles: list[str] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter()

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.addWidget(QLabel("Suhbatlar"))
        self.new_button = QPushButton("+ Yangi suhbat")
        self.new_button.clicked.connect(self._new_session)
        left_layout.addWidget(self.new_button)
        self.session_list = QListWidget()
        self.session_list.itemClicked.connect(self._open_session)
        left_layout.addWidget(self.session_list)
        splitter.addWidget(left)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 0, 0, 0)

        self.view = QTextBrowser()
        self.view.setOpenExternalLinks(True)
        self.view.setStyleSheet("background: white; border: 1px solid #ECEBF5; padding: 12px;")
        right_layout.addWidget(self.view)

        input_row = QWidget()
        input_layout = QHBoxLayout(input_row)
        input_layout.setContentsMargins(0, 8, 0, 0)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Yunaga yozing... (Enter — yuborish)")
        self.input.returnPressed.connect(self._send)
        self.send_button = QPushButton("Yuborish")
        self.send_button.setObjectName("primary")
        self.send_button.clicked.connect(self._send)
        input_layout.addWidget(self.input)
        input_layout.addWidget(self.send_button)
        right_layout.addWidget(input_row)
        splitter.addWidget(right)
        splitter.setSizes([240, 700])
        layout.addWidget(splitter)

        self._render_welcome()
        self.refresh()

    # ---------- ko'rinish ----------
    def _render(self) -> None:
        self.view.setHtml(
            "<div style='font-family: Segoe UI, sans-serif; font-size: 14px;'>"
            + "".join(self._bubbles)
            + "</div>"
        )
        self.view.moveCursor(QTextCursor.End)

    def _render_welcome(self) -> None:
        self.view.setHtml(
            "<div style='font-family: Segoe UI, sans-serif; font-size: 14px; color: #6B6B80;'>"
            "<p>Salom! Men Yuna. Eslatma, ovqat hisobi, rasm yoki hujjat — "
            "shunchaki yozing.</p></div>"
        )

    def _bubble(self, role: str, text: str) -> str:
        safe = html.escape(text)
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
    def refresh(self) -> None:
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
        self._render_welcome()

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
        if not self._bubbles:
            self._bubbles = []
            self._render()
        self._bubbles.append(self._bubble("user", text))
        self._render()
        self.send_button.setEnabled(False)
        QApplication.processEvents()

        try:
            data = self.api.chat(text, self.session_id)
            self.session_id = data["session_id"]
            self._bubbles.append(self._bubble("assistant", data["reply"]))
            self.refresh()
        except ApiError as exc:
            self._bubbles.append(self._bubble("assistant", f"Xatolik: {exc}"))
        finally:
            self.send_button.setEnabled(True)
            self._render()

    def add_system_message(self, text: str) -> None:
        if not self._bubbles:
            self._render_welcome()
            self._bubbles = []
        self._bubbles.append(self._bubble("assistant", text))
        self._render()


# ----------------------------- Eslatmalar -----------------------------
class RemindersPage(QWidget):
    def __init__(self, api: YunaAPI, parent=None) -> None:
        super().__init__(parent)
        self.api = api
        self._ids: list[int] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        form, form_layout = card_box("Yangi eslatma")
        self.text = QLineEdit()
        self.text.setPlaceholderText("Nima eslatilsin? (masalan: dori ichish)")
        self.when = QDateTimeEdit()
        self.when.setCalendarPopup(True)
        self.when.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.when.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        add_button = QPushButton("Qo'shish")
        add_button.setObjectName("primary")
        add_button.clicked.connect(self._add)
        row = QHBoxLayout()
        row.addWidget(self.text, 2)
        row.addWidget(self.when, 1)
        row.addWidget(add_button)
        form_layout.addLayout(row)
        layout.addWidget(form)

        listed, listed_layout = card_box("Eslatmalar")
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Matn", "Vaqt", "Holat"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 340)
        self.table.setColumnWidth(1, 150)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        listed_layout.addWidget(self.table)

        actions = QHBoxLayout()
        refresh_button = QPushButton("Yangilash")
        refresh_button.clicked.connect(self.refresh)
        self.delete_button = QPushButton("Tanlanganni o'chirish")
        self.delete_button.setObjectName("danger")
        self.delete_button.clicked.connect(self._delete)
        actions.addWidget(refresh_button)
        actions.addWidget(self.delete_button)
        actions.addStretch(1)
        listed_layout.addLayout(actions)
        layout.addWidget(listed, 1)

    def refresh(self) -> None:
        try:
            items = self.api.reminders()
        except ApiError as exc:
            QMessageBox.warning(self, "Xato", str(exc))
            return
        self._ids = []
        self.table.setRowCount(0)
        labels = {"pending": "Kutilmoqda", "sent": "Yuborilgan", "cancelled": "Bekor"}
        for item in items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(item["text"]))
            self.table.setItem(row, 1, QTableWidgetItem(to_local_text(item["remind_at"])))
            self.table.setItem(row, 2, QTableWidgetItem(labels.get(item["status"], item["status"])))
            self._ids.append(int(item["id"]))

    def _add(self) -> None:
        text = self.text.text().strip()
        if not text:
            QMessageBox.information(self, "Diqqat", "Eslatma matnini yozing.")
            return
        moment = self.when.dateTime().toPython().astimezone()
        try:
            self.api.create_reminder(text, moment.isoformat())
        except ApiError as exc:
            QMessageBox.warning(self, "Xato", str(exc))
            return
        self.text.clear()
        self.refresh()

    def _delete(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._ids):
            QMessageBox.information(self, "Diqqat", "Avval jadvaldan eslatmani tanlang.")
            return
        try:
            self.api.delete_reminder(self._ids[row])
        except ApiError as exc:
            QMessageBox.warning(self, "Xato", str(exc))
            return
        self.refresh()


# ----------------------------- Ovqat -----------------------------
class FoodPage(QWidget):
    def __init__(self, api: YunaAPI, parent=None) -> None:
        super().__init__(parent)
        self.api = api

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        stats, stats_layout = card_box("Bugungi hisob")
        self.kcal = QLabel("0 / 0 kkal")
        self.kcal.setObjectName("big")
        stats_layout.addWidget(self.kcal)
        self.macros = QLabel("Oqsil 0 g · Yog' 0 g · Uglevod 0 g")
        self.macros.setObjectName("muted")
        stats_layout.addWidget(self.macros)
        layout.addWidget(stats)

        add, add_layout = card_box("Taom qo'shish")
        self.text = QLineEdit()
        self.text.setPlaceholderText("Masalan: tushlikda 1 kosa osh va non")
        self.text.returnPressed.connect(self._add)
        add_button = QPushButton("Qo'shish")
        add_button.setObjectName("primary")
        add_button.clicked.connect(self._add)
        row = QHBoxLayout()
        row.addWidget(self.text, 1)
        row.addWidget(add_button)
        add_layout.addLayout(row)
        self.hint = QLabel("")
        self.hint.setObjectName("muted")
        self.hint.setWordWrap(True)
        add_layout.addWidget(self.hint)
        layout.addWidget(add)

        meals, meals_layout = card_box("Taomlar")
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Taom turi", "Kkal"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        meals_layout.addWidget(self.table)
        layout.addWidget(meals, 1)

    def refresh(self) -> None:
        try:
            data = self.api.food_summary()
        except ApiError as exc:
            QMessageBox.warning(self, "Xato", str(exc))
            return
        totals = data.get("totals", {})
        self.kcal.setText(f"{totals.get('kcal', 0):.0f} / {data.get('goal_kcal', 0)} kkal")
        self.macros.setText(
            f"Oqsil {totals.get('protein', 0):.0f} g · "
            f"Yog' {totals.get('fat', 0):.0f} g · "
            f"Uglevod {totals.get('carbs', 0):.0f} g"
        )
        self.table.setRowCount(0)
        for meal in data.get("meals", []):
            row = self.table.rowCount()
            self.table.insertRow(row)
            name = MEAL_LABELS.get(meal.get("meal_type", ""), meal.get("meal_type", ""))
            self.table.setItem(row, 0, QTableWidgetItem(f"{name} ({meal.get('items', 0)} ta)"))
            self.table.setItem(row, 1, QTableWidgetItem(f"{meal.get('kcal', 0):.0f}"))

    def _add(self) -> None:
        text = self.text.text().strip()
        if not text:
            return
        try:
            data = self.api.log_food(text)
        except ApiError as exc:
            QMessageBox.warning(self, "Xato", str(exc))
            return
        self.text.clear()
        self.hint.setText(data.get("reply", ""))
        self.refresh()


# ----------------------------- Maslahat -----------------------------
class AdvicePage(QWidget):
    def __init__(self, api: YunaAPI, parent=None) -> None:
        super().__init__(parent)
        self.api = api

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        box, box_layout = card_box("Kunlik maslahat")
        self.date = QLabel("")
        self.date.setObjectName("muted")
        box_layout.addWidget(self.date)
        self.text = QTextBrowser()
        self.text.setStyleSheet("border: none; background: transparent; font-size: 15px;")
        box_layout.addWidget(self.text, 1)
        refresh_button = QPushButton("Yangilash")
        refresh_button.clicked.connect(self.refresh)
        box_layout.addWidget(refresh_button)
        layout.addWidget(box, 1)

    def refresh(self) -> None:
        try:
            data = self.api.advice_today()
        except ApiError as exc:
            self.text.setPlainText(str(exc))
            return
        self.date.setText(f"{to_local_text(data.get('date', ''))[:10]} sanasi uchun")
        self.text.setPlainText(data.get("text", ""))


# ----------------------------- Sozlamalar -----------------------------
class SettingsPage(QWidget):
    logged_out = Signal()

    def __init__(self, api: YunaAPI, parent=None) -> None:
        super().__init__(parent)
        self.api = api

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(12)

        profile, profile_layout = card_box("Profil")
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        self.name = QLineEdit()
        self.email = QLineEdit()
        self.language = QComboBox()
        for code, label in LANGUAGES.items():
            self.language.addItem(label, code)
        self.timezone = QComboBox()
        self.timezone.setEditable(True)
        self.timezone.addItems(TIMEZONES)
        grid.addWidget(QLabel("Ism"), 0, 0)
        grid.addWidget(self.name, 0, 1)
        grid.addWidget(QLabel("Email"), 1, 0)
        grid.addWidget(self.email, 1, 1)
        grid.addWidget(QLabel("Til"), 2, 0)
        grid.addWidget(self.language, 2, 1)
        grid.addWidget(QLabel("Vaqt zonasi"), 3, 0)
        grid.addWidget(self.timezone, 3, 1)
        profile_layout.addLayout(grid)
        layout.addWidget(profile)

        prefs, prefs_layout = card_box("Kundalik sozlamalar")
        prefs_grid = QGridLayout()
        prefs_grid.setHorizontalSpacing(12)
        prefs_grid.setVerticalSpacing(8)
        self.advice_time = QTimeEdit()
        self.advice_time.setDisplayFormat("HH:mm")
        self.kcal_goal = QSpinBox()
        self.kcal_goal.setRange(800, 6000)
        self.kcal_goal.setSingleStep(50)
        prefs_grid.addWidget(QLabel("Maslahat vaqti"), 0, 0)
        prefs_grid.addWidget(self.advice_time, 0, 1)
        prefs_grid.addWidget(QLabel("Kunlik kkal maqsadi"), 1, 0)
        prefs_grid.addWidget(self.kcal_goal, 1, 1)
        prefs_layout.addLayout(prefs_grid)
        save = QPushButton("Saqlash")
        save.setObjectName("primary")
        save.clicked.connect(self._save)
        prefs_layout.addWidget(save)
        layout.addWidget(prefs)

        password, password_layout = card_box("Parolni o'zgartirish")
        self.current_password = QLineEdit()
        self.current_password.setEchoMode(QLineEdit.Password)
        self.current_password.setPlaceholderText("Joriy parol")
        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.Password)
        self.new_password.setPlaceholderText("Yangi parol (kamida 6 belgi)")
        change = QPushButton("Parolni yangilash")
        change.clicked.connect(self._change_password)
        password_layout.addWidget(self.current_password)
        password_layout.addWidget(self.new_password)
        password_layout.addWidget(change)
        layout.addWidget(password)

        server, server_layout = card_box("Server manzili")
        self.server_url = QLineEdit()
        self.server_url.setPlaceholderText("http://192.168.0.102:8000")
        save_server = QPushButton("Manzilni saqlash")
        save_server.clicked.connect(self._save_server)
        server_layout.addWidget(self.server_url)
        server_layout.addWidget(save_server)
        hint = QLabel("Manzil o'zgarsa qaytadan kirish kerak bo'ladi.")
        hint.setObjectName("muted")
        server_layout.addWidget(hint)
        layout.addWidget(server)

        account, account_layout = card_box("Hisob")
        self.who = QLabel("")
        self.who.setObjectName("muted")
        account_layout.addWidget(self.who)
        logout = QPushButton("Hisobdan chiqish")
        logout.setObjectName("danger")
        logout.clicked.connect(self._logout)
        account_layout.addWidget(logout)
        layout.addWidget(account)

        layout.addStretch(1)
        scroll.setWidget(inner)
        outer.addWidget(scroll)

    def refresh(self) -> None:
        try:
            user = self.api.me()
        except ApiError:
            user = self.api.user or {}
        self.name.setText(user.get("name", ""))
        self.email.setText(user.get("email") or "")
        index = self.language.findData(user.get("language", "uz"))
        self.language.setCurrentIndex(max(0, index))
        self.timezone.setCurrentText(user.get("timezone", "Asia/Tashkent"))
        advice = str(user.get("advice_time") or "08:00:00")
        parsed = QTime.fromString(advice[:5], "HH:mm")
        self.advice_time.setTime(parsed if parsed.isValid() else QTime(8, 0))
        self.kcal_goal.setValue(int(user.get("kcal_goal") or 2200))
        self.server_url.setText(self.api.base_url)
        role = "Admin" if user.get("is_admin") else "Foydalanuvchi"
        self.who.setText(f"{user.get('name', '')} · {user.get('email') or ''} · {role}")

    def _save(self) -> None:
        fields = {
            "name": self.name.text().strip(),
            "email": self.email.text().strip(),
            "language": self.language.currentData(),
            "timezone": self.timezone.currentText().strip() or "Asia/Tashkent",
            "advice_time": self.advice_time.time().toString("HH:mm:ss"),
            "kcal_goal": self.kcal_goal.value(),
        }
        if not fields["name"]:
            QMessageBox.information(self, "Diqqat", "Ism bo'sh bo'lmasligi kerak.")
            return
        try:
            self.api.update_me(fields)
        except ApiError as exc:
            QMessageBox.warning(self, "Xato", str(exc))
            return
        QMessageBox.information(self, "Tayyor", "Sozlamalar saqlandi.")
        self.refresh()

    def _change_password(self) -> None:
        if not self.current_password.text() or len(self.new_password.text()) < 6:
            QMessageBox.information(self, "Diqqat", "Yangi parol kamida 6 belgi bo'lsin.")
            return
        try:
            self.api.change_password(self.current_password.text(), self.new_password.text())
        except ApiError as exc:
            QMessageBox.warning(self, "Xato", str(exc))
            return
        self.current_password.clear()
        self.new_password.clear()
        QMessageBox.information(self, "Tayyor", "Parol yangilandi.")

    def _save_server(self) -> None:
        url = self.server_url.text().strip()
        if not url.startswith("http"):
            QMessageBox.information(self, "Diqqat", "Manzil http:// yoki https:// bilan boshlansin.")
            return
        if url.rstrip("/") == self.api.base_url:
            QMessageBox.information(self, "Tayyor", "Manzil o'zgarmadi.")
            return
        self.api.set_base_url(url)
        self.api.forget_session()
        QMessageBox.information(self, "Tayyor", "Manzil saqlandi. Qaytadan kiring.")
        self.logged_out.emit()

    def _logout(self) -> None:
        answer = QMessageBox.question(self, "Chiqish", "Hisobdan chiqasizmi?")
        if answer != QMessageBox.Yes:
            return
        self.api.forget_session()
        self.logged_out.emit()


# ----------------------------- Admin -----------------------------
class AdminPage(QWidget):
    def __init__(self, api: YunaAPI, parent=None) -> None:
        super().__init__(parent)
        self.api = api

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        stats, stats_layout = card_box("Statistika")
        self.stats_row = QGridLayout()
        stats_layout.addLayout(self.stats_row)
        layout.addWidget(stats)

        users, users_layout = card_box("Foydalanuvchilar")
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Ism", "Email", "Rol"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(1, 220)
        self.table.setColumnWidth(2, 260)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        users_layout.addWidget(self.table)
        refresh_button = QPushButton("Yangilash")
        refresh_button.clicked.connect(self.refresh)
        users_layout.addWidget(refresh_button)
        layout.addWidget(users, 1)

    def refresh(self) -> None:
        try:
            stats = self.api.admin_stats()
            users = self.api.admin_users()
        except ApiError as exc:
            QMessageBox.warning(self, "Xato", str(exc))
            return

        while self.stats_row.count():
            item = self.stats_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        labels = [
            ("Foydalanuvchi", stats.get("users", 0)),
            ("Qurilma", stats.get("devices", 0)),
            ("Suhbat", stats.get("sessions", 0)),
            ("Xabar", stats.get("messages", 0)),
            ("Eslatma", stats.get("reminders", 0)),
            ("Ovqat yozuvi", stats.get("food_logs", 0)),
        ]
        for index, (label, value) in enumerate(labels):
            holder = QVBoxLayout()
            number = QLabel(str(value))
            number.setObjectName("big")
            caption = QLabel(label)
            caption.setObjectName("muted")
            holder.addWidget(number)
            holder.addWidget(caption)
            box = QWidget()
            box.setLayout(holder)
            self.stats_row.addWidget(box, 0, index)

        self.table.setRowCount(0)
        for user in users:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(user["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(user["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(user.get("email") or "—"))
            self.table.setItem(
                row, 3, QTableWidgetItem("Admin" if user.get("is_admin") else "Foydalanuvchi")
            )


# ----------------------------- Asosiy oyna -----------------------------
class MainWindow(QMainWindow):
    logged_out = Signal()

    def __init__(self, api: YunaAPI) -> None:
        super().__init__()
        self.api = api
        self.setWindowTitle("Y.U.N.A")
        self.resize(1060, 720)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(210)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(14, 18, 14, 18)
        side_layout.setSpacing(6)

        brand = QLabel("Y.U.N.A")
        brand.setObjectName("brand")
        side_layout.addWidget(brand)
        tagline = QLabel("Shaxsiy yordamchingiz")
        tagline.setObjectName("muted")
        side_layout.addWidget(tagline)
        side_layout.addSpacing(14)

        self.stack = QStackedWidget()
        self.pages: dict[str, QWidget] = {}
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)

        sections = ["Suhbat", "Eslatmalar", "Ovqat", "Maslahat", "Sozlamalar"]
        if (api.user or {}).get("is_admin"):
            sections.append("Admin")

        for index, name in enumerate(sections):
            button = QPushButton(name)
            button.setObjectName("nav")
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            self.group.addButton(button, index)
            side_layout.addWidget(button)
            page = self._make_page(name)
            self.pages[name] = page
            self.stack.addWidget(page)
            button.clicked.connect(lambda _=False, n=name: self.go(n))

        side_layout.addStretch(1)
        user = api.user or {}
        who = QLabel(user.get("name") or "")
        who.setObjectName("muted")
        side_layout.addWidget(who)
        logout = QPushButton("Chiqish")
        logout.clicked.connect(self._logout)
        side_layout.addWidget(logout)

        layout.addWidget(sidebar)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(18, 18, 18, 18)
        content_layout.addWidget(self.stack)
        layout.addWidget(content, 1)

        self.go("Suhbat")
        self._start_ws()

    def _make_page(self, name: str) -> QWidget:
        if name == "Suhbat":
            self.chat_page = ChatPage(self.api, self)
            return self.chat_page
        if name == "Eslatmalar":
            return RemindersPage(self.api, self)
        if name == "Ovqat":
            return FoodPage(self.api, self)
        if name == "Maslahat":
            return AdvicePage(self.api, self)
        if name == "Sozlamalar":
            page = SettingsPage(self.api, self)
            page.logged_out.connect(self._logout)
            return page
        return AdminPage(self.api, self)

    def go(self, name: str) -> None:
        page = self.pages.get(name)
        if page is None:
            return
        self.stack.setCurrentWidget(page)
        buttons = self.group.buttons()
        index = list(self.pages).index(name)
        if index < len(buttons):
            buttons[index].setChecked(True)
        if hasattr(page, "refresh"):
            try:
                page.refresh()
            except ApiError as exc:
                QMessageBox.warning(self, "Xato", str(exc))

    # ---------- WebSocket ----------
    def _start_ws(self) -> None:
        self.ws = WSThread(self.api.ws_url())
        self.ws.message.connect(self._on_ws)
        self.ws.start()

    def _on_ws(self, payload: dict) -> None:
        kind = payload.get("type")
        if kind == "reminder":
            self.chat_page.add_system_message(f"⏰ {payload.get('text', '')}")
        elif kind == "advice":
            self.chat_page.add_system_message(f"🌸 {payload.get('text', '')}")

    def _logout(self) -> None:
        self.api.forget_session()
        self.logged_out.emit()

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
    app.setStyleSheet(QSS)
    icon = QIcon(resource_path("icon.png"))
    if not icon.isNull():
        app.setWindowIcon(icon)

    api = YunaAPI(BASE_URL)
    state: dict = {}

    def show_login() -> None:
        login = LoginWindow(api)
        state["login"] = login
        login.success.connect(open_main)
        login.show()

    def open_main() -> None:
        try:
            api.me()
        except ApiError:
            pass
        window = MainWindow(api)
        state["window"] = window
        window.logged_out.connect(relogin)
        window.show()

    def relogin() -> None:
        window = state.pop("window", None)
        if window is not None:
            window.close()
        api.register_device()
        show_login()

    if api.restore_session():
        api.register_device()
        open_main()
    else:
        show_login()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
