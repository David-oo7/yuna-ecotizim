"""AI xizmati — provayder bilan YAGONA aloqa nuqtasi.

Boshqa hech qayerda `google.genai` import qilinmaydi.
Provayder almashsa faqat shu fayl o'zgaradi.

GEMINI_MOCK=true bo'lsa tarmoqqa chiqilmaydi (testlar va oflayn ish uchun).
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from app.config import settings
from app.services import persona

logger = logging.getLogger(__name__)


class AIUnavailable(Exception):
    """AI javob bera olmadi."""


@dataclass
class AIResult:
    reply: str
    actions: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, int] = field(default_factory=dict)


# --------------------------- sxema ---------------------------
RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "reply": {"type": "string"},
        "actions": {
            "type": "array",
            "maxItems": 3,
            "items": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": [
                            "reminder_create",
                            "reminder_cancel",
                            "food_log",
                            "app_open",
                            "none",
                        ],
                    },
                    "payload": {"type": "object"},
                },
                "required": ["type", "payload"],
            },
        },
    },
    "required": ["reply", "actions"],
}


# --------------------------- mock ---------------------------
FOOD_TABLE: dict[str, tuple[float, float, float, float]] = {
    # nom: (kkal, oqsil, yog', uglevod) — 1 birlik uchun
    "non": (80, 2.5, 1.0, 15.0),
    "tuxum": (70, 6.0, 5.0, 0.5),
    "osh": (620, 18.0, 22.0, 88.0),
    "suv": (0, 0, 0, 0),
    "choy": (2, 0, 0, 0.5),
    "kofe": (5, 0.3, 0, 0.7),
    "olma": (52, 0.3, 0.2, 14.0),
    "banan": (89, 1.1, 0.3, 23.0),
    "guruch": (340, 7.0, 1.0, 74.0),
    "go'sht": (250, 26.0, 15.0, 0.0),
    "salat": (45, 1.5, 2.0, 5.0),
}

KNOWN_APPS: dict[str, str] = {
    "telegram": "org.telegram.messenger",
    "youtube": "com.google.android.youtube",
    "instagram": "com.instagram.android",
    "whatsapp": "com.whatsapp",
    "kamera": "com.android.camera",
    "kalkulyator": "com.android.calculator2",
}


def _num(text: str, name: str) -> int:
    match = re.search(r"(\d+)\s*(?:ta|dona)?\s*" + re.escape(name), text)
    return int(match.group(1)) if match else 1


def _meal_type(text: str) -> str:
    low = text.lower()
    if "nonushta" in low or "ertalab" in low:
        return "breakfast"
    if "tushlik" in low:
        return "lunch"
    if "kechki" in low or "kechqurun" in low:
        return "dinner"
    return "snack"


def _mock_food(text: str) -> list[dict[str, Any]]:
    low = text.lower()
    items: list[dict[str, Any]] = []
    for name, (kcal, protein, fat, carbs) in FOOD_TABLE.items():
        if name in low:
            count = _num(low, name)
            items.append(
                {
                    "name": name,
                    "amount_text": f"{count} ta",
                    "grams": None,
                    "kcal": kcal * count,
                    "protein": protein * count,
                    "fat": fat * count,
                    "carbs": carbs * count,
                    "meal_type": _meal_type(text),
                    "confidence": "medium",
                }
            )
    return items


def _mock_reply(text: str, mode: str, image: bool = False, audio: bool = False) -> AIResult:
    low = text.lower().strip()
    actions: list[dict[str, Any]] = []

    if audio:
        return AIResult(reply=f"Siz dedingiz: «{text}». Sizga qanday yordam beraman?")

    if image:
        return AIResult(
            reply="Rasmni ko'rdim. Unda matn va obyektlar bor — aniqroq savol bersangiz, "
            "batafsil tushuntiraman."
        )

    if "eslat" in low:
        clean = re.sub(r"\beslat(ing|ingiz|aman|ib qo'y|ib qo'yaman)?\b", "", text).strip(" .,-")
        clean = re.sub(r"\s+", " ", clean).strip(" .,-") or "Eslatma"
        if "daqiqadan keyin" in low:
            minutes = re.search(r"(\d+)\s*daqiqadan", low)
            when = f"in {minutes.group(1) if minutes else '5'} minutes"
        elif "ertaga" in low:
            when = "tomorrow 09:00"
        elif "soat" in low:
            hour = re.search(r"soat\s*(\d{1,2})", low)
            when = f"tomorrow {int(hour.group(1)):02d}:00" if hour else "in 5 minutes"
        else:
            when = "in 5 minutes"
        actions.append({"type": "reminder_create", "payload": {"text": clean, "when": when}})
        return AIResult(
            reply=f"Yaxshi, eslataman: «{clean}».", actions=actions
        )

    if "bekor" in low and "eslat" in low:
        actions.append({"type": "reminder_cancel", "payload": {}})
        return AIResult(reply="Eslatmani bekor qildim.", actions=actions)

    if "yedim" in low or any(k in low for k in FOOD_TABLE) or "ichdim" in low:
        items = _mock_food(text)
        if items:
            actions.append({"type": "food_log", "payload": {"items": items}})
            total = sum(i["kcal"] for i in items)
            names = ", ".join(i["name"] for i in items)
            return AIResult(
                reply=f"{names} — jami ~{total:.0f} kkal deb hisobladim. "
                "Raqamlar taxminiy.",
                actions=actions,
            )

    if "och" in low or "ochib" in low:
        for app_name, pkg in KNOWN_APPS.items():
            if app_name in low:
                actions.append(
                    {"type": "app_open", "payload": {"app_name": app_name, "package_name": pkg}}
                )
                return AIResult(
                    reply=f"{app_name.capitalize()} ni ochyapman.", actions=actions
                )

    if mode == "code" or "kod" in low:
        return AIResult(
            reply="Mana namuna:\n\n```python\n# faylni o'qish\ndef oqi(yol: str) -> str:\n"
            "    with open(yol, encoding='utf-8') as f:\n        return f.read()\n```"
        )

    if low in {"salom", "assalomu alaykum", "salom yuna", "hello", "привет"}:
        return AIResult(reply=persona.GREETING)

    return AIResult(
        reply=f"Tushundim: «{text[:120]}». Yana biror narsa kerakmi?"
    )


# --------------------------- real ---------------------------
def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise AIUnavailable("AI noto'g'ri javob qaytardi") from None
        data = json.loads(match.group(0))
    if not isinstance(data, dict) or "reply" not in data:
        raise AIUnavailable("AI javobida reply maydoni yo'q")
    data.setdefault("actions", [])
    return data


async def _gemini(
    prompt: str,
    system: str,
    model: str,
    image_bytes: bytes | None = None,
    image_mime: str = "image/jpeg",
    audio_bytes: bytes | None = None,
    audio_mime: str = "audio/m4a",
    force_json: bool = True,
) -> tuple[dict[str, Any] | str, dict[str, int]]:
    if not settings.gemini_api_key:
        raise AIUnavailable("GEMINI_API_KEY sozlanmagan")

    def _call() -> tuple[dict[str, Any] | str, dict[str, int]]:
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:  # pragma: no cover
            raise AIUnavailable("google-genai o'rnatilmagan") from exc

        client = genai.Client(api_key=settings.gemini_api_key)
        parts: list[Any] = []
        if image_bytes:
            parts.append(types.Part.from_bytes(data=image_bytes, mime_type=image_mime))
        if audio_bytes:
            parts.append(types.Part.from_bytes(data=audio_bytes, mime_type=audio_mime))
        parts.append(types.Part(text=prompt))

        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.6,
            max_output_tokens=2048,
        )
        if force_json:
            config.response_mime_type = "application/json"
            config.response_schema = RESPONSE_SCHEMA

        response = client.models.generate_content(
            model=model, contents=parts, config=config
        )
        usage: dict[str, int] = {}
        meta = getattr(response, "usage_metadata", None)
        if meta:
            usage = {
                "input_tokens": getattr(meta, "prompt_token_count", 0) or 0,
                "output_tokens": getattr(meta, "candidates_token_count", 0) or 0,
            }
        text = (response.text or "").strip()
        if not text:
            raise AIUnavailable("AI bo'sh javob qaytardi")
        if force_json:
            return _extract_json(text), usage
        return text, usage

    try:
        return await asyncio.wait_for(asyncio.to_thread(_call), timeout=60)
    except AIUnavailable:
        raise
    except asyncio.TimeoutError as exc:
        raise AIUnavailable("AI javobi juda kechikdi") from exc
    except Exception as exc:  # pragma: no cover - tashqi xizmat
        logger.warning("Gemini xatosi: %s", exc)
        raise AIUnavailable("AI xizmati vaqtincha ishlamayapti") from exc


# --------------------------- ommaviy API ---------------------------
def _history_text(history: list[dict[str, str]]) -> str:
    lines = []
    for item in history[-20:]:
        who = "foydalanuvchi" if item["role"] == "user" else "Yuna"
        lines.append(f"{who}: {item['content'][:1200]}")
    return "\n".join(lines)


async def respond(
    text: str,
    history: list[dict[str, str]],
    mode: str = "auto",
    user_name: str | None = None,
) -> AIResult:
    """Matnli suhbat: reply + actions."""
    if settings.gemini_mock or not settings.gemini_api_key:
        result = await asyncio.to_thread(_mock_reply, text, mode)
        result.usage = {
            "input_tokens": len(text) // 4,
            "output_tokens": len(result.reply) // 4,
        }
        return result

    prompt = (
        f"{_history_text(history)}\n\n"
        f"foydalanuvchi: {text}\n\n"
        "Yuqoridagi suhbatga javob ber. Faqat JSON qaytar: "
        '{"reply": "...", "actions": [...]}'
    )
    data, usage = await _gemini(
        prompt, persona.system_prompt(mode, user_name), settings.gemini_model_text
    )
    assert isinstance(data, dict)
    return AIResult(
        reply=str(data["reply"]).strip(),
        actions=data.get("actions") or [],
        usage=usage,
    )


async def explain_image(
    image_bytes: bytes, question: str | None, user_name: str | None = None
) -> str:
    if settings.gemini_mock or not settings.gemini_api_key:
        return _mock_reply(question or "rasm", "auto", image=True).reply
    prompt = question or "Bu rasmda nima bor? O'zbek tilida qisqa tushuntir."
    text, _ = await _gemini(
        prompt,
        persona.system_prompt("auto", user_name),
        settings.gemini_model_vision,
        image_bytes=image_bytes,
        force_json=False,
    )
    return str(text).strip()


async def transcribe(audio_bytes: bytes, mime: str = "audio/m4a") -> str:
    if settings.gemini_mock or not settings.gemini_api_key:
        return "salom yuna"
    text, _ = await _gemini(
        "Quyidagi ovozni so'zma-so'z o'zbek lotin alifbosida yoz. Faqat matn qaytar.",
        "Sen aniq transkripsiya qiluvchi vositachisan.",
        settings.gemini_model_audio,
        audio_bytes=audio_bytes,
        audio_mime=mime,
        force_json=False,
    )
    return str(text).strip()


async def daily_advice(
    user_name: str, food_totals: dict[str, float], reminders_count: int, recent: list[str]
) -> str:
    if settings.gemini_mock or not settings.gemini_api_key:
        return (
            f"{user_name}, bugun 2 stakan suv ichishni unutmang. "
            "Kichik qadamlar katta natija beradi."
        )
    prompt = (
        f"Foydalanuvchi: {user_name}\n"
        f"Kechagi ovqat jami: {food_totals}\n"
        f"Bugungi eslatmalar soni: {reminders_count}\n"
        f"Oxirgi maslahatlar: {recent}\n\n"
        "Bitta qisqa (2 jumladan ko'p bo'lmagan), takrorlanmaydigan, foydali "
        "kundalik maslahat yoz. Faqat JSON: {\"reply\": \"...\", \"actions\": []}"
    )
    data, _ = await _gemini(
        prompt, persona.system_prompt("auto", user_name), settings.gemini_model_text
    )
    assert isinstance(data, dict)
    return str(data["reply"]).strip()


async def docx_changes(
    paragraphs: list[str], instruction: str
) -> dict[str, Any]:
    """Hujjat tahriri uchun strukturali o'zgarishlar."""
    if settings.gemini_mock or not settings.gemini_api_key:
        changes = []
        if paragraphs:
            changes.append(
                {"target": "p:0", "new_text": paragraphs[0] + " (tahrirlandi)"}
            )
        return {"changes": changes, "notes": "Mock tahrir"}

    numbered = "\n".join(f"p:{i} = {p[:1500]}" for i, p in enumerate(paragraphs))
    prompt = (
        f"Ko'rsatma: {instruction}\n\nHujjat paragraflari:\n{numbered}\n\n"
        "Faqat o'zgargan paragraflarni qaytar. Sxema: "
        '{"changes": [{"target": "p:3", "new_text": "..."} | '
        '{"target": "p:5", "delete": true}], "notes": "qisqa izoh"}'
    )
    schema = {
        "type": "object",
        "properties": {
            "changes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "target": {"type": "string"},
                        "new_text": {"type": "string"},
                        "delete": {"type": "boolean"},
                    },
                    "required": ["target"],
                },
            },
            "notes": {"type": "string"},
        },
        "required": ["changes"],
    }
    if not settings.gemini_api_key:
        raise AIUnavailable("GEMINI_API_KEY sozlanmagan")

    def _call() -> dict[str, Any]:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.gemini_api_key)
        config = types.GenerateContentConfig(
            system_instruction=persona.system_prompt(),
            temperature=0.3,
            response_mime_type="application/json",
            response_schema=schema,
        )
        response = client.models.generate_content(
            model=settings.gemini_model_text, contents=[prompt], config=config
        )
        return _extract_json(response.text or "{}")

    try:
        return await asyncio.wait_for(asyncio.to_thread(_call), timeout=120)
    except AIUnavailable:
        raise
    except Exception as exc:  # pragma: no cover
        logger.warning("Gemini (docx) xatosi: %s", exc)
        raise AIUnavailable("Hujjatni tahrirlashda AI javob bermadi") from exc
