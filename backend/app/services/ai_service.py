"""AI xizmati — OpenRouter bilan YAGONA aloqa nuqtasi.

Boshqa hech qayerda provayder SDK'si import qilinmaydi.
Provayder almashsa faqat shu fayl o'zgaradi.

Model vazifaga qarab AVTOMATIK tanlanadi (chat, kod, rasm, Word, ovoz).
Birinchi model band bo'lsa (429), xato bersa yoki javob bo'sh qaytsa —
zanjirdagi keyingi bepul modelga o'tadi.

AI_MOCK=true bo'lsa (yoki OPENROUTER_API_KEY bo'lmasa) tarmoqqa chiqilmaydi
— testlar va oflayn ish uchun tayyor javoblar qaytariladi.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

import httpx

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


# --------------------------- model tanlash ---------------------------
# Vazifa -> bepul modellar zanjiri (birinchi ishlamasa keyingisiga o'tiladi).
TASK_MODELS: dict[str, tuple[str, ...]] = {
    "chat": (
        "nvidia/nemotron-3-ultra-550b-a55b:free",
        "baidu/ernie-5.5-flash-preview:free",
        "google/gemma-4-31b-it:free",
    ),
    "code": (
        "cohere/north-mini-code:free",
        "recursive/flint-v1.0:free",
        "nvidia/nemotron-3-ultra-550b-a55b:free",
    ),
    "vision": (
        "nvidia/nemotron-3.5-super-vl:free",
        "google/gemma-4-31b-it:free",
        "inclusionai/ling-3.2-flash:free",
    ),
    "doc": (
        "dots-studio/dots-3-note-preview:free",
        "nvidia/nemotron-3-ultra-550b-a55b:free",
        "google/gemma-4-31b-it:free",
    ),
    "audio": (
        "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
        "google/gemma-4-26b-a4b-it:free",
    ),
}

# .env orqali qo'lda almashtirish (bo'sh bo'lsa avtomatik zanjir ishlatiladi).
_MODEL_OVERRIDES: dict[str, str] = {
    "chat": "ai_model_chat",
    "code": "ai_model_code",
    "vision": "ai_model_vision",
    "doc": "ai_model_doc",
    "audio": "ai_model_audio",
}

_CODE_HINTS = re.compile(
    r"```|\bdef\s+\w+\s*\(|\bfunction\s+\w+\s*\(|\bclass\s+\w+|\bimport\s+\w+"
    r"|\bSELECT\b[\s\S]{0,80}\bFROM\b|\b(?:kod|code|skript|script|dastur)\b"
    r"|\b(?:python|javascript|typescript|java|kotlin|sql|html|css|c\+\+|php|golang)\b",
    re.IGNORECASE,
)


def _model_chain(task: str) -> list[str]:
    models = list(TASK_MODELS.get(task, TASK_MODELS["chat"]))
    override = getattr(settings, _MODEL_OVERRIDES.get(task, ""), "") or ""
    override = override.strip()
    if override:
        models = [override] + [m for m in models if m != override]
    # Takrorlanmasin
    seen: set[str] = set()
    return [m for m in models if not (m in seen or seen.add(m))]


def _auto_task(text: str, mode: str) -> str:
    """Matn va rejimga qarab vazifani aniqlaydi."""
    if mode == "code":
        return "code"
    if _CODE_HINTS.search(text or ""):
        return "code"
    return "chat"


def _audio_format(mime: str) -> str:
    mime = (mime or "").lower()
    if "wav" in mime:
        return "wav"
    if "mpeg" in mime or "mp3" in mime:
        return "mp3"
    if "ogg" in mime or "opus" in mime:
        return "ogg"
    if "webm" in mime:
        return "webm"
    return "m4a"


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


# --------------------------- real (OpenRouter) ---------------------------
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


def _content_text(content: Any) -> str:
    """Javob matni: ba'zi provayderlar bo'laklar ro'yxatini qaytaradi."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text") or ""))
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts)
    return ""


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        # OpenRouter statistikasi uchun (majburiy emas)
        "HTTP-Referer": settings.app_base_url or "https://github.com/David-oo7/yuna-ecotizim",
        "X-Title": persona.YUNA_DISPLAY_NAME,
    }


async def _post(
    model: str,
    messages: list[dict[str, Any]],
    *,
    temperature: float,
    max_tokens: int,
    force_json: bool,
    timeout: float,
) -> tuple[str, dict[str, int]]:
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if force_json:
        payload["response_format"] = {"type": "json_object"}

    url = f"{settings.openrouter_base_url.rstrip('/')}/chat/completions"
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, json=payload, headers=_headers())
        if (
            response.status_code == 400
            and force_json
            and "response_format" in response.text.lower()
        ):
            # Model strukturali JSON'ni qo'llamaydi — oddiy rejimda qayta so'raymiz
            payload.pop("response_format", None)
            response = await client.post(url, json=payload, headers=_headers())
        response.raise_for_status()
        data = response.json()

    choices = data.get("choices") or []
    if not choices:
        raise AIUnavailable("AI bo'sh javob qaytardi")
    text = _content_text((choices[0].get("message") or {}).get("content")).strip()
    if not text:
        raise AIUnavailable("AI bo'sh javob qaytardi")

    raw_usage = data.get("usage") or {}
    usage = {
        "input_tokens": int(raw_usage.get("prompt_tokens") or 0),
        "output_tokens": int(raw_usage.get("completion_tokens") or 0),
    }
    usage["total_tokens"] = usage["input_tokens"] + usage["output_tokens"]
    return text, usage


async def _complete(
    task: str,
    messages: list[dict[str, Any]],
    *,
    temperature: float = 0.6,
    max_tokens: int = 2048,
    force_json: bool = False,
    timeout: float = 90.0,
) -> tuple[dict[str, Any] | str, dict[str, int]]:
    """Vazifaga mos modelni tanlab, zanjir bo'ylab urinadi."""
    if not settings.openrouter_api_key:
        raise AIUnavailable("OPENROUTER_API_KEY sozlanmagan")

    last_error = "noma'lum xato"
    for model in _model_chain(task):
        try:
            text, usage = await _post(
                model,
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                force_json=force_json,
                timeout=timeout,
            )
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            last_error = f"{model}: HTTP {status}"
            logger.warning("OpenRouter %s → HTTP %s", model, status)
            if status == 429:
                await asyncio.sleep(0.6)
            continue
        except (httpx.HTTPError, ValueError) as exc:
            last_error = f"{model}: {exc}"
            logger.warning("OpenRouter %s ulanish xatosi: %s", model, exc)
            continue
        except AIUnavailable as exc:
            last_error = f"{model}: {exc}"
            continue

        if force_json:
            try:
                parsed = _extract_json(text)
            except (AIUnavailable, json.JSONDecodeError) as exc:
                last_error = f"{model}: JSON xato ({exc})"
                logger.warning("OpenRouter %s noto'g'ri JSON", model)
                continue
            logger.info("AI javob: %s (%s)", model, task)
            return parsed, usage

        logger.info("AI javob: %s (%s)", model, task)
        return text, usage

    logger.error("Barcha AI modellari ishlamadi (%s): %s", task, last_error)
    raise AIUnavailable("AI xizmati vaqtincha ishlamayapti")


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
    """Matnli suhbat: reply + actions. Model avtomatik tanlanadi."""
    if settings.ai_mock or not settings.openrouter_api_key:
        result = await asyncio.to_thread(_mock_reply, text, mode)
        result.usage = {
            "input_tokens": len(text) // 4,
            "output_tokens": len(result.reply) // 4,
        }
        return result

    task = _auto_task(text, mode)
    prompt = (
        f"{_history_text(history)}\n\n"
        f"foydalanuvchi: {text}\n\n"
        "Yuqoridagi suhbatga javob ber. Faqat JSON qaytar: "
        '{"reply": "...", "actions": [...]}'
    )
    data, usage = await _complete(
        task,
        [
            {"role": "system", "content": persona.system_prompt(mode, user_name)},
            {"role": "user", "content": prompt},
        ],
        temperature=0.6 if task != "code" else 0.2,
        force_json=True,
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
    if settings.ai_mock or not settings.openrouter_api_key:
        return _mock_reply(question or "rasm", "auto", image=True).reply

    prompt = question or "Bu rasmda nima bor? O'zbek tilida qisqa tushuntir."
    encoded = base64.b64encode(image_bytes).decode()
    messages = [
        {"role": "system", "content": persona.system_prompt("auto", user_name)},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}},
            ],
        },
    ]
    text, _ = await _complete("vision", messages, temperature=0.4, max_tokens=1024, timeout=120.0)
    return str(text).strip()


async def transcribe(audio_bytes: bytes, mime: str = "audio/m4a") -> str:
    if settings.ai_mock or not settings.openrouter_api_key:
        return "salom yuna"

    encoded = base64.b64encode(audio_bytes).decode()
    messages = [
        {
            "role": "system",
            "content": "Sen aniq transkripsiya qiluvchi vositachisan.",
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Quyidagi ovozni so'zma-so'z o'zbek lotin alifbosida yoz. "
                    "Faqat matn qaytar.",
                },
                {
                    "type": "input_audio",
                    "input_audio": {"data": encoded, "format": _audio_format(mime)},
                },
            ],
        },
    ]
    text, _ = await _complete("audio", messages, temperature=0.1, max_tokens=1024, timeout=120.0)
    return str(text).strip()


async def daily_advice(
    user_name: str, food_totals: dict[str, float], reminders_count: int, recent: list[str]
) -> str:
    if settings.ai_mock or not settings.openrouter_api_key:
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
        'kundalik maslahat yoz. Faqat JSON: {"reply": "...", "actions": []}'
    )
    data, _ = await _complete(
        "chat",
        [
            {"role": "system", "content": persona.system_prompt("auto", user_name)},
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,
        force_json=True,
    )
    assert isinstance(data, dict)
    return str(data["reply"]).strip()


async def docx_changes(
    paragraphs: list[str], instruction: str
) -> dict[str, Any]:
    """Hujjat tahriri uchun strukturali o'zgarishlar (Word uchun alohida model)."""
    if settings.ai_mock or not settings.openrouter_api_key:
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
    data, _ = await _complete(
        "doc",
        [
            {"role": "system", "content": persona.system_prompt()},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=4096,
        force_json=True,
        timeout=120.0,
    )
    assert isinstance(data, dict)
    if "changes" not in data:
        raise AIUnavailable("Hujjatni tahrirlashda AI javob bermadi")
    return data
