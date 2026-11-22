"""Y.U.N.A — Windows ilovasi (PySide6).

Bo'limlar: Bugun, Chat, Eslatmalar, Ovqat, Hujjat, Maslahat, Sozlamalar (+ Admin).

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
from PySide6.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QFont,
    QIcon,
    QPainter,
    QPen,
    QPixmap,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QDateTimeEdit,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
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
ACCENT = "#8B6CFF"
ACCENT_SOFT = "#2B2840"
TEAL = "#3FD7C4"
GREEN = "#6BE39B"
BG = "#14141C"
SIDEBAR_BG = "#1A1A26"
CARD_BG = "#1F1F2C"
CARD_BORDER = "#2B2B3D"
TEXT = "#ECECF5"
MUTED = "#8E8EA8"

MEAL_LABELS = {
    "breakfast": "Nonushta",
    "lunch": "Tushlik",
    "dinner": "Kechki ovqat",
    "snack": "Gazak",
}
LANGUAGES = {"uz": "O'zbekcha", "ru": "Русский", "en": "English"}
TIMEZONES = ["Asia/Tashkent", "Asia/Samarkand", "Asia/Almaty", "Europe/Moscow", "UTC"]

QSS = f"""
QWidget {{ background: {BG}; color: {TEXT}; font-family: "Segoe UI", sans-serif; font-size: 13px; }}
QLabel, QCheckBox, QRadioButton {{ background: transparent; }}
QFrame#sidebar {{ background: {SIDEBAR_BG}; border: none; }}
QFrame#card {{ background: {CARD_BG}; border: 1px solid {CARD_BORDER}; border-radius: 16px; }}
QFrame#advice {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #8B6CFF, stop:1 #6A45E8);
    border: none; border-radius: 18px;
}}
QLabel#cardTitle {{ font-size: 15px; font-weight: 600; color: {TEXT}; }}
QLabel#brand {{ font-size: 25px; font-weight: 800; color: {TEAL}; }}
QLabel#welcome {{ font-size: 27px; font-weight: 800; color: {TEXT}; }}
QLabel#muted {{ color: {MUTED}; }}
QLabel#big {{ font-size: 26px; font-weight: 700; color: {TEXT}; }}
QLabel#adviceTitle {{ color: white; font-size: 17px; font-weight: 700; }}
QLabel#adviceText {{ color: #F2EFFF; font-size: 14px; }}
QLabel#avatar {{
    background: #2A2A3C; border: 2px solid #3B3B52; border-radius: 21px; font-size: 20px;
}}
QPushButton#nav {{
    text-align: left; padding: 10px 14px; border: none; border-radius: 12px;
    background: transparent; color: #B9B9CE; font-size: 14px;
}}
QPushButton#nav:hover {{ background: #232332; color: {TEXT}; }}
QPushButton#nav:checked {{ background: {ACCENT_SOFT}; color: white; font-weight: 600; }}
QPushButton {{
    padding: 9px 16px; border-radius: 11px; border: 1px solid #34344A;
    background: #262636; color: {TEXT};
}}
QPushButton:hover {{ border-color: {ACCENT}; }}
QPushButton#primary {{
    background: {ACCENT}; color: white; border: none; font-weight: 600;
}}
QPushButton#primary:hover {{ background: #7A57F5; }}
QPushButton#gradient {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {TEAL}, stop:1 {GREEN});
    color: #06231F; border: none; border-radius: 12px; font-weight: 700; padding: 11px 18px;
}}
QPushButton#chip {{
    background: #262636; border: 1px solid #34344A; border-radius: 12px;
    padding: 10px 14px; color: {TEXT};
}}
QPushButton#ghost {{
    background: rgba(255, 255, 255, 38); border: none; border-radius: 10px;
    color: white; padding: 4px 8px; font-size: 16px;
}}
QPushButton#danger {{ color: #FF8A80; border-color: #5A3236; background: transparent; }}
QLineEdit, QComboBox, QSpinBox, QTimeEdit, QDateTimeEdit {{
    background: #262636; border: 1px solid #34344A; border-radius: 11px;
    padding: 8px 10px; min-height: 20px; selection-background-color: {ACCENT};
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTimeEdit:focus, QDateTimeEdit:focus {{
    border-color: {ACCENT};
}}
QComboBox QAbstractItemView {{
    background: #262636; color: {TEXT}; border: 1px solid #34344A;
    selection-background-color: {ACCENT_SOFT};
}}
QListWidget, QTableWidget, QTextBrowser {{
    background: #1B1B28; border: 1px solid {CARD_BORDER}; border-radius: 14px;
}}
QListWidget::item {{ padding: 8px; border-radius: 8px; }}
QListWidget::item:selected {{ background: {ACCENT_SOFT}; color: white; }}
QTableWidget {{ gridline-color: #262636; }}
QTableWidget::item {{ padding: 6px; }}
QTableWidget::item:selected {{ background: {ACCENT_SOFT}; color: white; }}
QHeaderView::section {{
    background: #22222F; border: none; border-bottom: 1px solid {CARD_BORDER};
    padding: 8px; color: {MUTED};
}}
QProgressBar {{ background: #2C2C3E; border: none; border-radius: 5px; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 4px; }}
QScrollBar::handle:vertical {{ background: #34344A; border-radius: 5px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollArea {{ border: none; background: transparent; }}
QToolTip {{ background: #2B2B3D; color: {TEXT}; border: 1px solid #3A3A52; }}
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


# ----------------------------- Bugun (uy) -----------------------------
MONTHS_UZ = [
    "yanvar",
    "fevral",
    "mart",
    "aprel",
    "may",
    "iyun",
    "iyul",
    "avgust",
    "sentabr",
    "oktabr",
    "noyabr",
    "dekabr",
]


class KcalRing(QWidget):
    """Kkal halqasi: iste'mol qilingan va maqsad nisbati."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(176, 176)
        self._consumed = 0.0
        self._goal = 2200.0

    def set_values(self, consumed: float, goal: float) -> None:
        self._consumed = max(0.0, float(consumed or 0))
        self._goal = float(goal or 0) or 2200.0
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(15, 15, -15, -15)

        track = QPen(QColor("#2C2C3E"), 13)
        track.setCapStyle(Qt.RoundCap)
        painter.setPen(track)
        painter.drawArc(rect, 0, 360 * 16)

        ratio = min(1.0, self._consumed / self._goal) if self._goal else 0.0
        if ratio > 0:
            gradient = QConicalGradient(rect.center(), 120)
            gradient.setColorAt(0.0, QColor(TEAL))
            gradient.setColorAt(0.55, QColor(GREEN))
            gradient.setColorAt(1.0, QColor(TEAL))
            arc = QPen(QBrush(gradient), 13)
            arc.setCapStyle(Qt.RoundCap)
            painter.setPen(arc)
            painter.drawArc(rect, 90 * 16, int(-360 * 16 * ratio))

        painter.setPen(QColor(TEXT))
        painter.setFont(QFont("Segoe UI", 17, QFont.Bold))
        painter.drawText(self.rect().adjusted(0, -18, 0, -18), Qt.AlignCenter, "Kkal")
        painter.setPen(QColor(MUTED))
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(
            self.rect().adjusted(0, 32, 0, 32),
            Qt.AlignCenter,
            f"({self._consumed:.0f} / {self._goal:.0f} kcal)",
        )


def today_text() -> str:
    now = datetime.now()
    return f"Bugun {now.day}-{MONTHS_UZ[now.month - 1]}, {now.year}-yil"


def reminder_text(value: str, text: str) -> str:
    """Eslatma vaqtini 'Ertaga 09:00 dori ichish' ko'rinishida beradi."""
    try:
        moment = datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone()
    except Exception:
        return text
    days = (moment.date() - datetime.now().astimezone().date()).days
    if days == 0:
        prefix = "Bugun"
    elif days == 1:
        prefix = "Ertaga"
    elif days == -1:
        prefix = "Kecha"
    else:
        prefix = moment.strftime("%d.%m")
    return f"{prefix} {moment.strftime('%H:%M')} {text}"


class HomePage(QWidget):
    """Bugun: maslahat, ovqat balansi, eng yaqin eslatma va tezkor amallar."""

    def __init__(self, api: YunaAPI, open_page, parent=None) -> None:
        super().__init__(parent)
        self.api = api
        self.open_page = open_page
        self._bars: dict[str, tuple[QProgressBar, QLabel]] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(14)

        # --- sarlavha ---
        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(2)
        user = api.user or {}
        name = (user.get("name") or "").strip()
        welcome = QLabel(f"Xush kelibsiz, {name}!" if name else "Xush kelibsiz!")
        welcome.setObjectName("welcome")
        date_label = QLabel(today_text())
        date_label.setObjectName("muted")
        titles.addWidget(welcome)
        titles.addWidget(date_label)
        header.addLayout(titles)
        header.addStretch(1)
        for emoji in ("\U0001f63a", "\U0001f638", "\U0001f63b"):
            avatar = QLabel(emoji)
            avatar.setObjectName("avatar")
            avatar.setAlignment(Qt.AlignCenter)
            avatar.setFixedSize(42, 42)
            header.addWidget(avatar)
        layout.addLayout(header)

        # --- maslahat ---
        advice = QFrame()
        advice.setObjectName("advice")
        advice_layout = QVBoxLayout(advice)
        advice_layout.setContentsMargins(20, 16, 20, 18)
        advice_layout.setSpacing(10)
        advice_top = QHBoxLayout()
        icon = QLabel()
        pixmap = QPixmap(resource_path("icon.png"))
        if not pixmap.isNull():
            icon.setPixmap(pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        title = QLabel("Bugungi Maslahat")
        title.setObjectName("adviceTitle")
        refresh = QPushButton("\u21bb")
        refresh.setObjectName("ghost")
        refresh.setFixedSize(32, 28)
        refresh.setCursor(Qt.PointingHandCursor)
        refresh.clicked.connect(self.refresh)
        advice_top.addWidget(icon)
        advice_top.addWidget(title)
        advice_top.addStretch(1)
        advice_top.addWidget(refresh)
        advice_layout.addLayout(advice_top)
        self.advice_text = QLabel("Yuklanmoqda...")
        self.advice_text.setObjectName("adviceText")
        self.advice_text.setWordWrap(True)
        advice_layout.addWidget(self.advice_text)
        layout.addWidget(advice)

        # --- ovqat balansi ---
        balance, balance_layout = card_box()
        balance_row = QHBoxLayout()
        balance_row.setSpacing(22)
        self.ring = KcalRing()
        balance_row.addWidget(self.ring)
        bars = QVBoxLayout()
        bars.setSpacing(12)
        for key, label, color, limit in (
            ("protein", "Oqsil", TEAL, 120.0),
            ("fat", "Yog'", GREEN, 80.0),
            ("carbs", "Uglevod", "#7DE0A8", 250.0),
        ):
            holder = QWidget()
            holder_layout = QVBoxLayout(holder)
            holder_layout.setContentsMargins(0, 0, 0, 0)
            holder_layout.setSpacing(5)
            row = QHBoxLayout()
            name = QLabel(label)
            name.setStyleSheet(f"color: {TEXT}; font-size: 13px;")
            value = QLabel("0 g")
            value.setStyleSheet(f"color: {MUTED}; font-size: 12px;")
            row.addWidget(name)
            row.addStretch(1)
            row.addWidget(value)
            holder_layout.addLayout(row)
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setTextVisible(False)
            bar.setFixedHeight(9)
            bar.setStyleSheet(
                "QProgressBar { background: #2C2C3E; border: none; border-radius: 5px; }"
                f"QProgressBar::chunk {{ background: {color}; border-radius: 5px; }}"
            )
            holder_layout.addWidget(bar)
            self._bars[key] = (bar, value)
            bars.addWidget(holder)
        bars.addStretch(1)
        balance_row.addLayout(bars, 1)
        balance_layout.addLayout(balance_row)
        layout.addWidget(balance)

        # --- eng yaqin eslatma va tezkor amallar ---
        reminder, reminder_layout = card_box()
        head = QLabel("Eng yaqin eslatma")
        head.setStyleSheet(f"color: {TEXT}; font-size: 15px; font-weight: 600;")
        self.reminder_text = QLabel("Yuklanmoqda...")
        self.reminder_text.setObjectName("muted")
        self.reminder_text.setWordWrap(True)
        reminder_layout.addWidget(head)
        reminder_layout.addWidget(self.reminder_text)
        actions = QHBoxLayout()
        actions.setSpacing(8)
        for text, target in (("\U0001f399  Ovoz", "Chat"), ("\U0001f5bc  Rasm", "Chat"), ("\U0001f4c4  Hujjat", "Hujjat")):
            chip = QPushButton(text)
            chip.setObjectName("chip")
            chip.setCursor(Qt.PointingHandCursor)
            chip.clicked.connect(lambda _=False, t=target: self.open_page(t))
            actions.addWidget(chip)
        actions.addStretch(1)
        new_reminder = QPushButton("+  Yangi Eslatma")
        new_reminder.setObjectName("gradient")
        new_reminder.setCursor(Qt.PointingHandCursor)
        new_reminder.clicked.connect(lambda: self.open_page("Eslatmalar"))
        actions.addWidget(new_reminder)
        reminder_layout.addLayout(actions)
        layout.addWidget(reminder)

        layout.addStretch(1)
        scroll.setWidget(inner)
        outer.addWidget(scroll)

    # ---------- ma'lumot ----------
    def _set_macro(self, key: str, value: float, limit: float) -> None:
        bar, label = self._bars[key]
        ratio = min(1.0, max(0.0, value / limit)) if limit else 0.0
        bar.setValue(int(ratio * 100))
        label.setText(f"{value:.0f} g")

    def refresh(self) -> None:
        try:
            advice = self.api.advice_today()
            self.advice_text.setText(advice.get("text") or "Maslahat hozircha yo'q.")
        except ApiError:
            self.advice_text.setText("Maslahatni yuklab bo'lmadi. Internet aloqasini tekshiring.")

        data: dict = {}
        try:
            data = self.api.food_summary()
        except ApiError:
            pass
        totals = data.get("totals", {}) if data else {}
        goal = float((data or {}).get("goal_kcal") or 0)
        self.ring.set_values(float(totals.get("kcal") or 0), goal or 2200)
        self._set_macro("protein", float(totals.get("protein") or 0), 120.0)
        self._set_macro("fat", float(totals.get("fat") or 0), 80.0)
        self._set_macro("carbs", float(totals.get("carbs") or 0), 250.0)

        try:
            pending = [r for r in self.api.reminders() if r.get("status") == "pending"]
        except ApiError:
            pending = []
        if pending:
            first = min(pending, key=lambda r: str(r.get("remind_at") or ""))
            self.reminder_text.setText(reminder_text(first.get("remind_at") or "", first.get("text") or ""))
        else:
            self.reminder_text.setText("Hozircha eslatma yo'q. Yangi eslatma qo'shing.")


# ----------------------------- Suhbat -----------------------------
class ChatPage(QWidget):
    def __init__(self, api: YunaAPI, parent=None) -> None:
        super().__init__(parent)
        self.api = api
        self.session_id: int | None = None
        self._bubbles: list[str] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        head_widget = QWidget()
        head_widget.setFixedHeight(40)
        header = QHBoxLayout(head_widget)
        header.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Chat")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {TEXT};")
        self.online = QLabel("\u25cf  WebSocket onlayn")
        self.online.setStyleSheet(
            f"color: {TEAL}; background: #16302C; border-radius: 11px;"
            "padding: 5px 12px; font-size: 12px;"
        )
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.online)
        layout.addWidget(head_widget)

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
        self.view.setStyleSheet(
            "background: #1B1B28; border: 1px solid #2B2B3D; border-radius: 14px; padding: 12px;"
        )
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
            "<div style='font-family: Segoe UI, sans-serif; font-size: 14px; color: #8E8EA8;'>"
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
            "<span style='background:#262636;border:1px solid #2B2B3D;color:#ECECF5;"
            "padding:8px 12px;border-radius:12px;display:inline-block;max-width:70%;'>"
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


# ----------------------------- Hujjat -----------------------------
class DocumentsPage(QWidget):
    """Word (.docx) yuklash, AI bilan tahrirlash va versiyalarni boshqarish."""

    def __init__(self, api: YunaAPI, parent=None) -> None:
        super().__init__(parent)
        self.api = api
        self._ids: list[int] = []
        self._names: dict[int, str] = {}
        self._selected: int | None = None
        self._picked: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        upload, upload_layout = card_box("Word fayl yuklash")
        row = QHBoxLayout()
        self.pick_button = QPushButton("Fayl tanlash")
        self.pick_button.clicked.connect(self._pick)
        self.picked_label = QLabel("Fayl tanlanmagan")
        self.picked_label.setObjectName("muted")
        self.upload_button = QPushButton("Yuklash")
        self.upload_button.setObjectName("primary")
        self.upload_button.clicked.connect(self._upload)
        row.addWidget(self.pick_button)
        row.addWidget(self.picked_label, 1)
        row.addWidget(self.upload_button)
        upload_layout.addLayout(row)
        hint = QLabel("Faqat .docx fayl qabul qilinadi. Har bir yuklash yangi versiya sifatida saqlanadi.")
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        upload_layout.addWidget(hint)
        layout.addWidget(upload)

        edit, edit_layout = card_box("AI bilan tahrirlash")
        self.instruction = QLineEdit()
        self.instruction.setPlaceholderText(
            "Masalan: matnni rasmiy uslubda qayta yoz va imlo xatolarini tuzat"
        )
        self.instruction.returnPressed.connect(self._edit)
        self.edit_button = QPushButton("Tahrirlash")
        self.edit_button.setObjectName("primary")
        self.edit_button.clicked.connect(self._edit)
        edit_row = QHBoxLayout()
        edit_row.addWidget(self.instruction, 1)
        edit_row.addWidget(self.edit_button)
        edit_layout.addLayout(edit_row)
        self.selected_label = QLabel("Tahrirlash uchun hujjat tanlanmagan")
        self.selected_label.setObjectName("muted")
        edit_layout.addWidget(self.selected_label)
        layout.addWidget(edit)

        documents, documents_layout = card_box("Hujjatlar va versiyalar")
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Fayl", "Versiya", "Hajm", "Sana"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 360)
        self.table.setColumnWidth(1, 90)
        self.table.setColumnWidth(2, 100)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._on_select)
        documents_layout.addWidget(self.table, 1)

        actions = QHBoxLayout()
        refresh_button = QPushButton("Yangilash")
        refresh_button.clicked.connect(self.refresh)
        download_button = QPushButton("Tanlanganni yuklab olish")
        download_button.clicked.connect(self._download)
        actions.addWidget(refresh_button)
        actions.addWidget(download_button)
        actions.addStretch(1)
        documents_layout.addLayout(actions)
        layout.addWidget(documents, 1)

    def refresh(self) -> None:
        try:
            items = self.api.documents()
        except ApiError as exc:
            QMessageBox.warning(self, "Xato", str(exc))
            return
        self._ids = []
        self._names = {}
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        selected_row = -1
        for item in items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            file_id = int(item["file_id"])
            self.table.setItem(row, 0, QTableWidgetItem(item["original_name"]))
            self.table.setItem(row, 1, QTableWidgetItem(f"v{item['version']}"))
            self.table.setItem(
                row, 2, QTableWidgetItem(f"{int(item.get('size_bytes') or 0) / 1024:.0f} KB")
            )
            self.table.setItem(row, 3, QTableWidgetItem(to_local_text(item.get("created_at") or "")))
            self._ids.append(file_id)
            self._names[file_id] = item["original_name"]
            if self._selected == file_id:
                selected_row = row
        self.table.blockSignals(False)
        if selected_row >= 0:
            self.table.selectRow(selected_row)
        elif self._ids and self._selected not in self._ids:
            self._selected = self._ids[0]
            self.table.selectRow(0)
        self._update_selected_label()

    def _update_selected_label(self) -> None:
        if self._selected is None:
            self.selected_label.setText("Tahrirlash uchun hujjat tanlanmagan")
            return
        name = self._names.get(self._selected, f"#{self._selected}")
        self.selected_label.setText(f"Tanlangan hujjat: {name} (#{self._selected})")

    def _on_select(self) -> None:
        row = self.table.currentRow()
        if 0 <= row < len(self._ids):
            self._selected = self._ids[row]
            self._update_selected_label()

    def _pick(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Word fayl tanlash", "", "Word hujjat (*.docx)")
        if path:
            self._picked = path
            self.picked_label.setText(os.path.basename(path))

    def _upload(self) -> None:
        if not self._picked:
            QMessageBox.information(self, "Diqqat", "Avval .docx faylni tanlang.")
            return
        if not self._picked.lower().endswith(".docx"):
            QMessageBox.information(self, "Diqqat", "Faqat .docx fayl yuklanadi.")
            return
        self.upload_button.setEnabled(False)
        QApplication.processEvents()
        try:
            data = self.api.upload_document(self._picked)
        except (ApiError, OSError) as exc:
            QMessageBox.warning(self, "Xato", str(exc))
            return
        finally:
            self.upload_button.setEnabled(True)
        self._selected = int(data["file_id"])
        self._picked = None
        self.picked_label.setText("Fayl tanlanmagan")
        self.refresh()
        QMessageBox.information(self, "Tayyor", f"Fayl yuklandi: v{data['version']}")

    def _edit(self) -> None:
        instruction = self.instruction.text().strip()
        if self._selected is None:
            QMessageBox.information(self, "Diqqat", "Tahrirlash uchun hujjatni jadvaldan tanlang.")
            return
        if len(instruction) < 2:
            QMessageBox.information(self, "Diqqat", "Tahrir ko'rsatmasini yozing.")
            return
        self.edit_button.setEnabled(False)
        self.edit_button.setText("Tahrirlanmoqda...")
        QApplication.processEvents()
        try:
            data = self.api.edit_document(self._selected, instruction)
        except ApiError as exc:
            QMessageBox.warning(self, "Xato", str(exc))
            return
        finally:
            self.edit_button.setEnabled(True)
            self.edit_button.setText("Tahrirlash")
        self._selected = int(data["file_id"])
        self.instruction.clear()
        self.refresh()
        QMessageBox.information(self, "Tayyor", f"Yangi versiya tayyor: v{data['version']}")

    def _download(self) -> None:
        if self._selected is None:
            QMessageBox.information(self, "Diqqat", "Jadvaldan hujjatni tanlang.")
            return
        name = self._names.get(self._selected, "hujjat.docx")
        path, _ = QFileDialog.getSaveFileName(self, "Saqlash", name, "Word hujjat (*.docx)")
        if not path:
            return
        try:
            self.api.download_document(self._selected, path)
        except (ApiError, OSError) as exc:
            QMessageBox.warning(self, "Xato", str(exc))
            return
        QMessageBox.information(self, "Tayyor", f"Fayl saqlandi:\n{path}")


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
        self.resize(1240, 800)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(238)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(16, 22, 16, 18)
        side_layout.setSpacing(4)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)
        logo = QLabel()
        pixmap = QPixmap(resource_path("icon.png"))
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        brand = QLabel("Yuna")
        brand.setObjectName("brand")
        brand_row.addWidget(logo)
        brand_row.addWidget(brand)
        brand_row.addStretch(1)
        side_layout.addLayout(brand_row)
        tagline = QLabel("Shaxsiy yordamchingiz")
        tagline.setObjectName("muted")
        side_layout.addWidget(tagline)
        side_layout.addSpacing(18)

        self.stack = QStackedWidget()
        self.pages: dict[str, QWidget] = {}
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)

        sections = [
            ("Bugun", "\U0001f3e0  Bugun"),
            ("Chat", "\U0001f4ac  Chat"),
            ("Eslatmalar", "\U0001f4cb  Eslatmalar"),
            ("Ovqat", "\U0001f374  Ovqat"),
            ("Hujjat", "\U0001f4c4  Hujjatlar"),
            ("Maslahat", "\U0001f4a1  Maslahat"),
            ("Sozlamalar", "\u2699  Sozlamalar"),
        ]
        if (api.user or {}).get("is_admin"):
            sections.append(("Admin", "\U0001f6e1  Admin"))

        for index, (name, label) in enumerate(sections):
            button = QPushButton(label)
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
        who.setStyleSheet(f"color: {TEXT}; font-size: 14px; font-weight: 600;")
        role = QLabel("Admin" if user.get("is_admin") else user.get("email") or "Foydalanuvchi")
        role.setObjectName("muted")
        side_layout.addWidget(who)
        side_layout.addWidget(role)
        side_layout.addSpacing(8)
        logout = QPushButton("Chiqish")
        logout.clicked.connect(self._logout)
        side_layout.addWidget(logout)

        layout.addWidget(sidebar)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(22, 20, 22, 20)
        content_layout.addWidget(self.stack)
        layout.addWidget(content, 1)

        self.go("Bugun")
        self._start_ws()

    def _make_page(self, name: str) -> QWidget:
        if name == "Bugun":
            return HomePage(self.api, self.go, self)
        if name == "Chat":
            self.chat_page = ChatPage(self.api, self)
            return self.chat_page
        if name == "Eslatmalar":
            return RemindersPage(self.api, self)
        if name == "Ovqat":
            return FoodPage(self.api, self)
        if name == "Maslahat":
            return AdvicePage(self.api, self)
        if name == "Hujjat":
            return DocumentsPage(self.api, self)
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
