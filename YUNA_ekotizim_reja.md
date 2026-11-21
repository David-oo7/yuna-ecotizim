# Y.U.N.A EKOTIZIMI — TO'LIQ QURILISH REJASI (v2)

> **Bu hujjat kim uchun:** loyihani quruvchi AI agent va uni boshqaruvchi inson uchun.
> **Qanday o'qiladi:** 1–2-bo'limni bir marta o'qib chiqing, keyin 10-bo'limdagi bosqichlar bo'yicha yuqoridan pastga yuring. Har bosqich oxirida "Tayyor mezoni" bajarilmasa, keyingisiga o'tmang.
> **Asosiy qoida:** hamma mantiq, AI kalitlari va ma'lumotlar faqat backendda. APK, Windows ilova va Telegram bot — yupqa mijozlar.

---

## 1. BIR QARASHDA

| Savol | Javob |
|---|---|
| Nima quriladi | Bitta backend + 3 mijoz (Android, Windows, Telegram) ishlaydigan yagona AI yordamchi ekotizimi |
| Yordamchining ismi | **Y.U.N.A** (talaffuzi "Yuna") — qiz bola shaxsiyati, o'zbek tilida |
| Kim uchun | Bitta egasi (Doston) va unga yaqin foydalanuvchilar — shaxsiy, kundalik yordamchi |
| Backend | Python 3.12 + FastAPI + PostgreSQL (Neon) |
| Hosting | Render (backend) + Cloudflare R2 (fayllar) |
| Vaqt | 6 bosqich, har biri 3–7 kun (to'liq stavkada ~6 hafta) |
| Natija | APK, `.exe`, ishlaydigan Telegram bot va bitta umumiy baza |

### 1.1. Ekotizim nima beradi (11 imkoniyat, bir jadvalda)

| № | Imkoniyat | Bosqich | Foydalanuvchi uchun bir jumlada |
|---|---|---|---|
| 1 | Word faylni AI bilan tahrirlash | 4 | "Shu hujjatni tuzat" — tayyor fayl qaytadi |
| 2 | Rasmni tushuntirish | 3 | Rasm yuboradi — Yuna o'zbekcha tushuntiradi |
| 3 | Dasturlash tillarini bilish | 3 | Kod so'raydi — ishlaydigan kod oladi |
| 4 | Kundalik eslatmalar | 3 | "Ertaga 9 da dori" — o'zi eslatadi |
| 5 | Kundalik maslahat | 3 | Har kuni ertalab bitta foydali maslahat |
| 6 | Oziq-ovqat hisobi | 3 | "1 kosa osh yedim" — kkal hisoblanadi |
| 7 | Telegramda javob yozish | 2 | Bot mijozlarga o'zi (yoki tasdiq bilan) javob beradi |
| 8 | APK: ilovalarni ochish | 5 | "Telegramni och" — telefonda ochiladi |
| 9 | Ovozli suhbat (o'zbekcha) | 5 | Gapirib yozadi, Yuna ovoz bilan javob beradi |
| 10 | Ishni qurilmadan qurilmaga ko'chirish | 5 | Telefonda boshlagan suhbatni kompyuterda davom ettiradi |
| 11 | Yagona shaxsiyat | 1 | Uch qurilmada ham bir xil "Yuna" |

### 1.2. Mahsulot soddaligi qoidalari (buzilmasin)

1. **Bitta ekran — chat.** APK va Windows'da asosiy ekran faqat suhbat. Boshqa hamma narsa (eslatma, ovqat, hujjat) shu chat ichidan tabiiy tilda chaqiriladi.
2. **Bitta tugma — mikrofon.** Ovozli rejim alohida sahifa emas, chat pastidagi tugma.
3. **Sozlash minimal.** Ro'yxatdan o'tish: ism + parol (yoki Telegram orqali kirish). Boshqa sozlama faqat "Sozlamalar" ichida, ixtiyoriy.
4. **Har javob 1 ekranga sig'adi.** Uzun javob kerak bo'lsa "batafsil" tugmasi bilan ochiladi.
5. **Xato bo'lsa — ayblov emas, yechim.** "Server bilan aloqa yo'q. Qayta urinish" — texnik kod emas, o'zbekcha tushunarli matn.

---

## 2. TEXNOLOGIYA TANLOVI (qat'iy, muqobilsiz)

Agent "yaxshiroq variant bormi?" deb vaqt sarflamasin — quyidagilar tanlangan.

| Qatlam | Tanlov | Versiya | Sabab |
|---|---|---|---|
| Backend | FastAPI + Uvicorn | 0.115 / 0.32 | Tez, async, avtomatik OpenAPI |
| Validatsiya | Pydantic v2 | 2.x | JSON shartnomalarni qat'iy tekshiradi |
| ORM | SQLAlchemy 2.0 (async) + asyncpg | 2.0 | Async, Alembic bilan mos |
| Migratsiya | Alembic | 1.13 | Baza versiyalarini boshqaradi |
| Baza | PostgreSQL 16 (Neon) | — | Bepul, ishonchli, JSONB bor |
| AI | OpenRouter (bepul modellar) | router | Chat, kod, rasm, Word, ovoz — vazifaga qarab avtomatik model |
| Telegram | aiogram 3 (webhook) | 3.15 | Async, FastAPI bilan bir jarayonda |
| Scheduler | APScheduler (AsyncIOScheduler) | 3.10 | Kichik yuk uchun Celery ortiqcha |
| Word | python-docx | 1.1 | Formatlashni saqlab tahrirlaydi |
| TTS | edge-tts (`uz-UZ-MadinaNeural`) | 7.x | Bepul, o'zbekcha ayol ovozi |
| STT | OpenRouter multimodal (`nemotron-3-nano-omni`) | — | Zanjir: model ishlamasa keyingisiga o'tadi |
| JWT | PyJWT | 2.9 | Oddiy va barqaror |
| Parol hash | argon2-cffi | 23.x | bcrypt/passlib muammolaridan xoli |
| Fayl ombori | Cloudflare R2 (S3 API, boto3) | 1.35 | Render diski vaqtinchalik |
| Push | Firebase Admin SDK (FCM v1) | 6.x | Android push |
| Android | Kotlin + Jetpack Compose + Retrofit | — | Rasmiy, zamonaviy |
| Windows | Python 3.12 + PySide6 | 6.7 | Bitta tilda, tez |
| Testlar | pytest + pytest-asyncio + httpx | — | Async endpointlarni sinaydi |

**Bitta qoida:** AI provayderi faqat `services/ai_service.py` ichida. Boshqa hech qayerda `google.genai` import qilinmaydi. Provayder almashsa — bitta fayl o'zgaradi.

---

## 3. ARXITEKTURA

```
  Android APK ─┐
               │  HTTPS/REST + WebSocket + FCM push
  Windows app ─┼──────►  BACKEND (FastAPI, bitta jarayon)  ──► PostgreSQL (Neon)
               │            │   │   │   │   │                   Cloudflare R2
  Telegram ────┘            │   │   │   │   └── APScheduler (eslatma, maslahat)
   (webhook)                │   │   │   └────── ai_service → Gemini (matn/rasm/audio)
                            │   │   └────────── stt_service / tts_service
                            │   └────────────── docx_service (python-docx)
                            └────────────────── auth, sessions, devices, commands
```

**Muhim oqim qoidalari**

- Har so'rov `Authorization: Bearer <access_token>` bilan keladi; `user_id` **token ichidan** olinadi, hech qachon so'rov tanasidan emas.
- Mijoz hech qachon AI'ga to'g'ridan-to'g'ri murojaat qilmaydi va hech qanday kalit saqlamaydi.
- Bir qurilmada yozilgan xabar WebSocket orqali ikkinchisiga darhol boradi; baza — yagona haqiqat manbai.
- Uzoq ishlar (docx tahrirlash, TTS) fon vazifasi sifatida bajariladi va natija push/WS bilan qaytadi.

---

## 4. PAPKA TUZILMASI

```
yuna/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI app, routerlar, startup/shutdown
│   │   ├── config.py              # Settings (pydantic-settings) — .env dan
│   │   ├── db.py                  # async engine, session dependency
│   │   ├── deps.py                # get_current_user, rate limit
│   │   ├── api/v1/
│   │   │   ├── auth.py  chat.py  vision.py  voice.py  docs.py
│   │   │   ├── reminders.py  advice.py  food.py  devices.py
│   │   │   ├── sessions.py  telegram.py  ws.py
│   │   ├── services/
│   │   │   ├── ai_service.py      # YAGONA AI kirish nuqtasi
│   │   │   ├── persona.py         # Y.U.N.A shaxsiyati (bir joyda)
│   │   │   ├── intents.py         # AI javobini amalga aylantirish
│   │   │   ├── docx_service.py    # docx o'qish/tahrirlash/versiya
│   │   │   ├── food_service.py    # ovqat hisobi
│   │   │   ├── reminder_service.py
│   │   │   ├── stt_service.py  tts_service.py
│   │   │   ├── push_service.py    # FCM
│   │   │   ├── storage_service.py # R2 yoki lokal disk (dev)
│   │   │   └── ws_manager.py      # WS ulanishlar reyestri
│   │   ├── models/                # SQLAlchemy modellari (jadval bo'yicha fayl)
│   │   ├── schemas/               # Pydantic so'rov/javob sxemalari
│   │   ├── bots/telegram/         # aiogram router, handlerlar
│   │   └── scheduler/jobs.py      # eslatma tekshiruvi, kunlik maslahat
│   ├── alembic/
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── android/                       # Kotlin loyihasi
├── windows/                       # PySide6 ilova
├── shared/api.md                  # API shartnomasi (shu hujjatdan ko'chirilgan)
└── docs/                          # qo'llanmalar, eskizlar
```

---

## 5. ATROF-MUHIT O'ZGARUVCHILARI

`backend/.env.example` — repo ichida turadi, haqiqiy `.env` **hech qachon** commit qilinmaydi.

```env
# --- Umumiy ---
APP_ENV=dev
APP_SECRET_KEY=change-me-64-random-chars
APP_BASE_URL=http://localhost:8000

# --- Baza ---
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/yuna

# --- JWT ---
JWT_ALGORITHM=HS256
ACCESS_TOKEN_TTL_MIN=15
REFRESH_TOKEN_TTL_DAYS=30

# --- AI (OpenRouter, bepul modellar) ---
OPENROUTER_API_KEY=
AI_MOCK=false
# Bo'sh bo'lsa model vazifaga qarab avtomatik tanlanadi:
AI_MODEL_CHAT=
AI_MODEL_CODE=
AI_MODEL_VISION=
AI_MODEL_DOC=
AI_MODEL_AUDIO=

# --- Telegram ---
TELEGRAM_BOT_TOKEN=
TELEGRAM_WEBHOOK_SECRET=

# --- Fayllar ---
STORAGE_DRIVER=local            # local | r2
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET=yuna-files
UPLOAD_MAX_MB=20

# --- Push ---
FCM_CREDENTIALS_JSON=           # service account JSON (bir qatorga siqilgan)
```

---

## 6. MA'LUMOTLAR BAZASI

Quyidagi SQL — `alembic` birinchi migratsiyasining mazmuni. Agent buni to'liq, o'zgartirmasdan yozadi.

```sql
-- ============ users ============
CREATE TABLE users (
    id            BIGSERIAL PRIMARY KEY,
    name          TEXT        NOT NULL,
    email         TEXT        UNIQUE,
    password_hash TEXT,
    telegram_id   BIGINT      UNIQUE,
    timezone      TEXT        NOT NULL DEFAULT 'Asia/Tashkent',
    language      TEXT        NOT NULL DEFAULT 'uz',
    advice_time   TIME        NOT NULL DEFAULT '08:00',
    kcal_goal     INTEGER     NOT NULL DEFAULT 2200,
    is_active     BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============ devices ============
CREATE TABLE devices (
    id            BIGSERIAL PRIMARY KEY,
    user_id       BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_uid    TEXT        NOT NULL,           -- mijoz generatsiya qilgan UUID
    type          TEXT        NOT NULL CHECK (type IN ('android','windows','telegram')),
    model         TEXT,
    fcm_token     TEXT,
    push_enabled  BOOLEAN     NOT NULL DEFAULT TRUE,
    last_seen_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, device_uid)
);

-- ============ refresh_tokens ============
CREATE TABLE refresh_tokens (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id   BIGINT      REFERENCES devices(id) ON DELETE SET NULL,
    token_hash  TEXT        NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    revoked_at  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============ sessions / messages ============
CREATE TABLE sessions (
    id             BIGSERIAL PRIMARY KEY,
    user_id        BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title          TEXT        NOT NULL DEFAULT 'Yangi suhbat',
    last_device_id BIGINT      REFERENCES devices(id) ON DELETE SET NULL,
    state_json     JSONB       NOT NULL DEFAULT '{}'::jsonb,  -- ochiq fayl, qoralama, oxirgi amal
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    archived_at    TIMESTAMPTZ
);
CREATE INDEX idx_sessions_user ON sessions (user_id, updated_at DESC);

CREATE TABLE messages (
    id         BIGSERIAL PRIMARY KEY,
    session_id BIGINT      NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    user_id    BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role       TEXT        NOT NULL CHECK (role IN ('user','assistant','system')),
    type       TEXT        NOT NULL DEFAULT 'text'
                           CHECK (type IN ('text','voice','image','file')),
    content    TEXT        NOT NULL,
    meta       JSONB       NOT NULL DEFAULT '{}'::jsonb,  -- file_id, lang, actions
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_messages_session ON messages (session_id, id);

-- ============ reminders ============
CREATE TABLE reminders (
    id           BIGSERIAL PRIMARY KEY,
    user_id      BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    text         TEXT        NOT NULL,
    remind_at    TIMESTAMPTZ NOT NULL,
    repeat_rule  TEXT        CHECK (repeat_rule IN ('daily','weekly','monthly')),
    channel      TEXT        NOT NULL DEFAULT 'both'
                             CHECK (channel IN ('push','telegram','both')),
    status       TEXT        NOT NULL DEFAULT 'pending'
                             CHECK (status IN ('pending','sent','cancelled','failed')),
    last_sent_at TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_reminders_due ON reminders (remind_at) WHERE status = 'pending';

-- ============ advice_log ============
CREATE TABLE advice_log (
    id         BIGSERIAL PRIMARY KEY,
    user_id    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    log_date   DATE   NOT NULL,
    text       TEXT   NOT NULL,
    channels   TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, log_date)
);

-- ============ food_logs ============
CREATE TABLE food_logs (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    eaten_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    meal_type   TEXT        NOT NULL CHECK (meal_type IN ('breakfast','lunch','dinner','snack')),
    name        TEXT        NOT NULL,
    amount_text TEXT,                          -- "1 kosa", "2 dona"
    grams       NUMERIC(7,1),
    kcal        NUMERIC(7,1) NOT NULL DEFAULT 0,
    protein     NUMERIC(7,1) NOT NULL DEFAULT 0,
    fat         NUMERIC(7,1) NOT NULL DEFAULT 0,
    carbs       NUMERIC(7,1) NOT NULL DEFAULT 0,
    source      TEXT        NOT NULL DEFAULT 'text'
                            CHECK (source IN ('text','voice','photo')),
    confidence  TEXT        NOT NULL DEFAULT 'medium'
                            CHECK (confidence IN ('low','medium','high')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_food_user_date ON food_logs (user_id, eaten_at);

-- ============ files (versiyalash) ============
CREATE TABLE files (
    id            BIGSERIAL PRIMARY KEY,
    user_id       BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_id     BIGINT      REFERENCES files(id) ON DELETE SET NULL,  -- oldingi versiya
    kind          TEXT        NOT NULL CHECK (kind IN ('docx','image','audio','pdf')),
    original_name TEXT        NOT NULL,
    storage_path  TEXT        NOT NULL,
    mime          TEXT        NOT NULL,
    size_bytes    BIGINT      NOT NULL,
    version       INTEGER     NOT NULL DEFAULT 1,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============ qurilma buyruqlari ============
CREATE TABLE device_commands (
    id               BIGSERIAL PRIMARY KEY,
    user_id          BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_device_id BIGINT      NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    command          TEXT        NOT NULL
                     CHECK (command IN ('open_app','open_url','notify','ping')),
    payload          JSONB       NOT NULL DEFAULT '{}'::jsonb,
    status           TEXT        NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending','delivered','done','failed','expired')),
    result           JSONB,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    delivered_at     TIMESTAMPTZ
);
CREATE INDEX idx_commands_pending ON device_commands (target_device_id)
    WHERE status IN ('pending','delivered');

-- ============ o'rnatilgan ilovalar ============
CREATE TABLE installed_apps (
    id           BIGSERIAL PRIMARY KEY,
    device_id    BIGINT      NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    app_name     TEXT        NOT NULL,
    package_name TEXT        NOT NULL,
    is_system    BOOLEAN     NOT NULL DEFAULT FALSE,
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (device_id, package_name)
);

-- ============ telegram chatlar ============
CREATE TABLE telegram_chats (
    id             BIGSERIAL PRIMARY KEY,
    chat_id        BIGINT      NOT NULL UNIQUE,
    user_id        BIGINT      REFERENCES users(id) ON DELETE SET NULL,
    mode           TEXT        NOT NULL DEFAULT 'manual'
                               CHECK (mode IN ('auto','manual')),
    memory_summary TEXT,
    is_blocked     BOOLEAN     NOT NULL DEFAULT FALSE,
    last_message_at TIMESTAMPTZ,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Bog'lanish qoidasi:** `messages`, `reminders`, `food_logs`, `files`, `sessions` — hammasida `user_id` bor. Har so'rovda `WHERE user_id = current_user.id` **majburiy**. Bu — ma'lumot izolyatsiyasining yagona kafolati.

---

## 7. API SHARTNOMASI (`/api/v1`)

### 7.1. Umumiy qoidalar

- Barcha javoblar JSON, UTF-8. Vaqtlar ISO-8601 (`2026-11-21T09:00:00+05:00`).
- Muvaffaqiyat: HTTP 200/201 + resursning o'zi (`{"id":1,...}`), ro'yxat: `{"items":[...],"next_cursor":null}`.
- Xato: HTTP 4xx/5xx + yagona format:
```json
{ "error": { "code": "VALIDATION", "message": "text maydoni bo'sh bo'lmasin", "field": "text" } }
```

| Kod | HTTP | Ma'nosi |
|---|---|---|
| `AUTH_REQUIRED` | 401 | Token yo'q |
| `TOKEN_EXPIRED` | 401 | Access token muddati tugadi → refresh qil |
| `AUTH_INVALID` | 401 | Login/parol xato |
| `FORBIDDEN` | 403 | Boshqa foydalanuvchi resursi |
| `NOT_FOUND` | 404 | Topilmadi |
| `VALIDATION` | 422 | Maydon xato |
| `RATE_LIMITED` | 429 | Juda ko'p so'rov (`Retry-After` sarlavhasi bilan) |
| `FILE_TOO_LARGE` | 413 | Hajm oshdi |
| `UNSUPPORTED_TYPE` | 415 | Format qo'llanmaydi |
| `AI_UNAVAILABLE` | 503 | AI javob bermadi, qayta urinish kerak |
| `INTERNAL` | 500 | Kutilmagan xato (foydalanuvchiga tafsilot ko'rsatilmaydi) |

### 7.2. Endpointlar ro'yxati

```
POST   /auth/register            ism, email|telegram, parol
POST   /auth/login               email + parol → access + refresh
POST   /auth/refresh             refresh → yangi juftlik (rotatsiya)
POST   /auth/logout              refresh bekor qilish
GET    /me                       profil
PATCH  /me                       ism, timezone, advice_time, kcal_goal

POST   /chat                     matnli suhbat (+ intent bajarish)
POST   /chat/stream              SSE oqim (5-bosqich)
GET    /sessions                 suhbatlar ro'yxati
GET    /sessions/{id}            xabarlar (sahifalab)
PATCH  /sessions/{id}            nomini o'zgartirish / arxivlash
POST   /sessions/{id}/handoff    boshqa qurilmaga "davom ettirish" belgisi

POST   /vision/explain           rasm + savol
POST   /voice/stt                audio → matn
POST   /voice/tts                matn → audio (mp3)
POST   /voice/chat               audio → matn + javob + audio

POST   /docs/upload              docx yuklash → file_id
POST   /docs/edit                file_id + ko'rsatma → yangi versiya
GET    /docs/{id}/download       imzolangan yuklash havolasi

GET    /reminders                ?status=pending
POST   /reminders                matn yoki tabiiy til
PATCH  /reminders/{id}           vaqt/matn/holat
DELETE /reminders/{id}

GET    /advice/today             bugungi maslahat (yo'q bo'lsa yaratadi)

POST   /food/log                 "2 non va 1 tuxum yedim"
GET    /food/summary?date=       kunlik jami + maqsad bilan taqqoslash
DELETE /food/logs/{id}

POST   /devices/register         device_uid, type, fcm_token
POST   /devices/apps/sync        package_name ro'yxati
POST   /devices/command          boshqa qurilmaga buyruq
GET    /devices                  qurilmalar ro'yxati

POST   /telegram/webhook/{secret}  Telegram yangilanishlari
WS     /ws                       real vaqt
GET    /health                   {"ok":true,"db":true,"ai":true}
```

### 7.3. Asosiy endpointlar — aniq shartnoma

**`POST /auth/login`**
```json
// so'rov
{ "email": "doston@example.com", "password": "••••••", "device_uid": "a1b2-..." }
// javob 200
{
  "access_token": "eyJ...", "refresh_token": "eyJ...",
  "token_type": "bearer", "expires_in": 900,
  "user": { "id": 1, "name": "Doston", "timezone": "Asia/Tashkent" }
}
```

**`POST /chat`**
```json
// so'rov
{ "session_id": 12, "text": "ertaga 9 da dori ichishni eslat", "mode": "auto", "device_uid": "a1b2-..." }
// mode: "auto" | "code"
// javob 200
{
  "session_id": 12,
  "message_id": 99,
  "reply": "Yaxshi, ertaga 09:00 da eslataman 🌸",
  "actions": [ { "type": "reminder_created", "id": 5 } ],
  "usage": { "input_tokens": 812, "output_tokens": 34 }
}
```
- `session_id` yuborilmasa — yangi sessiya yaratiladi va javobda qaytadi.
- AI'ga oxirgi 20 xabar + `persona` + `session.state_json` kontekst sifatida beriladi.

**`POST /voice/chat`** (multipart: `audio` fayl, ixtiyoriy `session_id`)
```json
{ "session_id": 12, "text": "salom yuna", "reply": "Salom, Doston!",
  "audio_url": "https://.../tts/abc.mp3", "actions": [] }
```

**`POST /docs/edit`**
```json
// so'rov
{ "file_id": 31, "instruction": "3-bo'limni qisqartir, xatolarni tuzat" }
// javob 202 (fon vazifasi)
{ "job_id": "b7c1", "status": "processing" }
// tayyor bo'lganda WS/push: { "type":"doc_ready", "file_id": 32, "version": 2 }
```

**`POST /devices/command`**
```json
{ "target_device_id": 4, "command": "open_app", "payload": { "package_name": "org.telegram.messenger" } }
// javob 202 → { "id": 77, "status": "pending" }
```

**`GET /food/summary?date=2026-11-21`**
```json
{ "date": "2026-11-21", "goal_kcal": 2200,
  "totals": { "kcal": 1430, "protein": 62, "fat": 41, "carbs": 187 },
  "meals": [ { "meal_type": "lunch", "items": 3, "kcal": 720 } ],
  "note": "Raqamlar taxminiy." }
```

### 7.4. WebSocket protokoli (`/ws`)

```
Ulanish: wss://<host>/ws?token=<access_token>   (yoki birinchi xabar bilan hello)

client → {"type":"hello","device_uid":"a1b2"}
server → {"type":"ready","user_id":1,"device_id":4}

client → {"type":"subscribe","session_id":12}
server → {"type":"message","session_id":12,"message":{...}}     // yangi xabar
server → {"type":"command","command":{"id":77,"command":"open_app","payload":{...}}}
client → {"type":"ack","command_id":77,"status":"done","result":{"ok":true}}
server → {"type":"doc_ready","file_id":32}
server → {"type":"ping"}   // 30 soniyada bir; 90 soniya javob bo'lmasa uziladi
```
Qayta ulanish: mijoz 1→2→4→8 soniya kutib qayta ulanadi va `subscribe`dan keyin `GET /sessions/{id}` bilan to'liq holatni oladi (WS faqat tezlik uchun, haqiqat manbai — baza).

---

## 8. Y.U.N.A SHAXSIYATI

`backend/app/services/persona.py` — **yagona manba**. APK, Windows, Telegram, TTS — hammasi shu yerdan oladi.

```python
YUNA_NAME = "Y.U.N.A"
YUNA_DISPLAY_NAME = "Yuna"

PERSONA_PROMPT = """
Sen — Y.U.N.A (talaffuzi "Yuna"), o'zbek qiz bolasi shaxsiyatidagi shaxsiy yordamchi.
Asoschising — Doston.

Ohang va uslub:
- Samimiy, mehribon, xotirjam. Haddan tashqari emoji ishlatma (javobda ko'pi bilan 1 ta).
- Qisqa va aniq gapir. Oddiy savolga 1-3 jumla. Faqat batafsil so'ralsa uzun yoz.
- O'zbek tilida (lotin alifbosida) gapir. Foydalanuvchi rus yoki ingliz tilida yozsa — o'sha tilda javob ber.
- Foydalanuvchini ismi bilan chaqirishing mumkin, lekin har jumlada emas.

Bilim va halollik:
- Bilmagan narsani o'ylab topma. "Buni aniq bilmayman" deb ayt va kerak bo'lsa qanday tekshirishni taklif qil.
- Tibbiy, huquqiy yoki moliyaviy masalada maslahat berma — umumiy ma'lumot ber va mutaxassisga murojaat qilishni ayt.
- Ovqat kaloriyasi kabi raqamlar taxminiy ekanini aytib qo'y.

Kod:
- Kod so'ralganda ishlaydigan, to'liq kod ber. Tilni foydalanuvchi aytmasa, vazifaga mos tilni tanla.
- Kod izohlarini o'zbekcha yoz. Kodni ```til blokida ber.
- "Bu yerda o'zingiz to'ldiring" kabi bo'sh joy qoldirma.

Amallar (actions):
- Sen faqat matn qaytarmaysan, balki JSON ham qaytarasan (schema beriladi).
- Foydalanuvchi eslatma, ovqat yoki ilova ochishni so'rasa — mos action qaytar.
- Ishonching komil bo'lmasa action qaytarma, savol ber.
"""

CODE_MODE_ADDITION = """
Hozir kod rejimi yoqilgan: javob to'liq ishlaydigan kod bo'lsin,
kerak bo'lsa qisqa tushuntirish bilan, lekin ortiqcha suhbat yo'q.
"""
```

**AI javob sxemasi (structured output)** — `intents.py` shu sxemani talab qiladi:

```json
{
  "reply": "foydalanuvchiga ko'rinadigan matn",
  "actions": [
    {
      "type": "reminder_create | reminder_cancel | food_log | app_open | none",
      "payload": { }
    }
  ]
}
```
- `actions` — ko'pi bilan 2 ta. `none` bo'lsa bo'sh massiv.
- Noto'g'ri JSON kelsa: 1 marta qayta so'raladi, keyin faqat `reply` ishlatiladi va `actions` tashlab yuboriladi (**hech qachon** taxminiy action bajarilmaydi).

---

## 9. FUNKSIYALAR — TEXNIK TAFSILOT

Har funksiya uchun: qanday ishlaydi, qaysi endpointlar, cheklovlar, "tayyor" mezoni.

### 9.1. Word faylni AI bilan tahrirlash
**Oqim:** yuklash → paragraflarni raqamlash → AI'ga strukturali JSON so'rovi → farqni qo'llash → yangi versiya.
1. `python-docx` bilan paragraflar `[0..n]` indekslanadi, jadvallar alohida (`table:0/row:2/cell:1`).
2. AI'ga faqat **indeks + matn + ko'rsatma** yuboriladi, butun fayl emas. Javob:
```json
{ "changes": [ { "target": "p:14", "new_text": "..." },
               { "target": "p:15", "delete": true } ],
  "notes": "3-bo'lim qisqartirildi" }
```
3. Qo'llashda `paragraph.text` almashadi, `run` formati birinchi run xususiyatlaridan saqlanadi (shrift, o'lcham). Yangi paragraf kerak bo'lsa `insert_paragraph_before`.
4. Har tahrir yangi `files` yozuvi: `version = oldingi + 1`, `parent_id = oldingi id`. Asl fayl **hech qachon** o'chirilmaydi.
5. Cheklov: `.docx` 20 MB gacha, 5000 paragrafgacha. `.doc` qabul qilinmaydi — foydalanuvchiga "docx ga saqlang" deyiladi.
**Tayyor mezoni:** 3 xil haqiqiy hujjatda (sarlavhali, jadvali, ro'yxatli) formatlash buzilmagan holda tahrirlanadi; versiya tarixi ko'rinadi.

### 9.2. Rasmni tushuntirish
- `POST /vision/explain` (multipart: `image`, ixtiyoriy `question`, `session_id`).
- Rasm serverga kelgach: JPEG'ga o'giriladi, uzun tomoni 1600px, sifat 85 (Pillow) — bu tezlik va token tejaydi.
- Rejimlar avtomatik aniqlanadi: kod skrinshoti → kod tahlili; matn rasmi → matnni ko'chirish + izoh; ovqat → 9.6 bilan bog'lanadi (kaloriya taxmini).
- Javob oddiy `reply` + `messages` ga `type='image'` yozuvi (rasm `file_id` bilan).
**Tayyor mezoni:** o'zbekcha savolga o'zbekcha, 1 ekranli javob; kod rasmidan ishlaydigan kod chiqadi.

### 9.3. Dasturlash tillarini bilish
- Alohida endpoint yo'q — `mode="code"` bayrog'i `PERSONA_PROMPT + CODE_MODE_ADDITION` ni qo'shadi.
- Mijozda kod bloklari monospace, "nusxa olish" tugmasi bilan. APK: `SelectionContainer`, Windows: `QPlainTextEdit` + clipboard tugmasi.
- Uzun kod (1500 token+) bo'lsa javob bo'laklarga bo'linadi va `code_chunk` meta bilan yuboriladi.
**Tayyor mezoni:** "Python'da faylni o'qi" so'roviga to'liq, ishga tushadigan kod; izohlar o'zbekcha.

### 9.4. Kundalik eslatmalar
- Yaratish: `POST /reminders` (`{"text":"dori ichish","when":"ertaga 09:00"}`) — `when` tabiiy matn bo'lsa AI uni `remind_at` + `repeat_rule` ga aylantiradi. Aniq ISO vaqt berilsa AI ishlatilmaydi (tezroq va arzon).
- Scheduler: har 30 soniyada `SELECT ... WHERE status='pending' AND remind_at <= now()` (SKIP LOCKED bilan) → yuborish → `status='sent'`, `repeat_rule` bo'lsa keyingi vaqtga yangi yozuv.
- Yetkazish: FCM (Android), WS (Windows ochiq bo'lsa), Telegram (`channel` ga qarab).
- Vaqt zonasi: hamma vaqt `users.timezone` da hisoblanadi, bazada `TIMESTAMPTZ`.
- Takrorlanish: `daily` +1 kun, `weekly` +7 kun, `monthly` keyingi oyning shu kuni (kun yo'q bo'lsa oxirgi kun).
**Tayyor mezoni:** 2 daqiqadan keyingi eslatma telefonga va Telegramga yetib keladi; takrorlanuvchi eslatma ertasi kuni yana keladi; bekor qilingan eslatma kelmaydi.

### 9.5. Kundalik maslahatlar
- Job har kuni 07:55 (Toshkent) ishlaydi va `advice_time` ga mos ravishda yuboradi.
- Kontekst: kechagi ovqat jami, bugungi eslatmalar soni, oxirgi 7 kun maslahatlari (takrorlanmasin), foydalanuvchi ismi.
- Natija `advice_log` ga yoziladi (kuniga 1 ta, `UNIQUE(user_id, log_date)`), keyin push/Telegram.
- `/advice/today` — bugungisi bo'lsa qaytaradi, bo'lmasa darhol yaratadi.
**Tayyor mezoni:** 3 kun ketma-ket maslahat keladi va takrorlanmaydi.

### 9.6. Oziq-ovqat hisobi
- Kirish: matn, ovoz transkripti yoki rasm.
- AI javobi (sxema bilan qat'iy):
```json
{ "items": [ { "name": "osh", "amount": "1 kosa", "grams": 350,
               "kcal": 620, "protein": 18, "fat": 22, "carbs": 88,
               "meal_type": "lunch", "confidence": "medium" } ],
  "reply": "1 kosa osh ~620 kkal deb hisobladim. Taxminiy raqam." }
```
- Har item `food_logs` ga alohida yoziladi. `confidence='low'` bo'lsa javobda "taxminiy" ta'kidlanadi.
- `GET /food/summary` kunlik jami + `kcal_goal` bilan farq (foizda).
- **Cheklov:** tibbiy maslahat yo'q, faqat hisob. AI'ga "dieta tuzma" so'rovi kelsa — umumiy ma'lumot + shifokor tavsiyasi.
**Tayyor mezoni:** "2 non va 1 tuxum" → 3 emas, 2 yozuv, jami mantiqiy; kunlik jami to'g'ri qo'shiladi.

### 9.7. Telegramda javob yozish
- aiogram webhook: `POST /telegram/webhook/{TELEGRAM_WEBHOOK_SECRET}` (secret yo'l va `X-Telegram-Bot-Api-Secret-Token` tekshiriladi).
- Chat topilmasa — yaratiladi, `mode='manual'`.
- `auto`: xabar → `memory_summary` + oxirgi 10 xabar → Yuna javobi → yuboriladi, xotira yangilanadi.
- `manual`: javob egasiga (asosiy foydalanuvchi) yuboriladi: "Javob varianti: ... [Yuborish] [Tahrirlash] [Rad]".
- Himoya: chat uchun 20 xabar/daqiqa limiti, `is_blocked` ro'yxati, uzunlik 4000 belgi.
- Mavjud bot kodi shu backendga ko'chiriladi — **bitta baza, bitta jarayon**.
**Tayyor mezoni:** auto rejimda bot mantiqiy javob beradi; manual rejimda egasi tasdiqlagandan keyingina yuboriladi; limit ishlaydi.

### 9.8. APK: ilovalarni ochish
- `PackageManager.getInstalledApplications()` → `POST /devices/apps/sync` (`[{"app_name":"Telegram","package_name":"org.telegram.messenger"}]`).
- "Telegramni och" → backend `installed_apps` dan `package_name` topadi (fuzzy match, AI yordamida) → `device_commands` yozuvi → FCM data-push yoki WS.
- APK buyruqni oladi → `Intent(ACTION_MAIN, CATEGORY_LAUNCHER)` bilan ochadi → `POST`/WS `ack` bilan natija qaytaradi.
- Murakkab harakat (tugma bosish, menyu) — **AccessibilityService**, foydalanuvchi Sozlamalardan qo'lda yoqadi. Faqat whitelist'dagi amallar.
- Android cheklovi: fonda ishga tushirish cheklangan → `foreground service` + `POST_NOTIFICATIONS` ruxsati + batareya optimizatsiyasidan chiqarish so'rovi.
**Tayyor mezoni:** telefonda 3 xil ilova ovozli buyruq bilan ochiladi; topilmasa Yuna "Telegram topilmadi, o'rnatilganmi?" deb so'raydi.

### 9.9. Ovozli suhbat (o'zbekcha)
- Oqim: mikrofon → `.m4a` (16 kHz, mono) → `POST /voice/chat` → STT → intent → TTS → matn + audio URL.
- **STT:** asosiy — OpenRouter multimodal modeli (bitta so'rovda transkript), zaxira — zanjirdagi keyingi model. `stt_service.py` da `transcribe(audio, lang) -> str` interfeysi, ikkala provayder shu interfeys ostida. **Aniqlikni o'lchash:** 10 ta real ovozli namuna, so'z xatosi foizi jadvalga yoziladi, eng yaxshisi qoladi.
- **TTS:** `edge-tts` `uz-UZ-MadinaNeural`, `rate="+8%"`. Natija mp3, R2/local'ga saqlanadi, `audio_url` qaytadi. Keshlash: matn hash bo'yicha bir xil javob qayta sintez qilinmaydi.
- Latency maqsadi: birinchi javob < 3 s (5-bosqichda SSE bilan < 1.5 s).
- "Hey Yuna" uyg'otuvchi so'z — **v2**, hozir emas.
**Tayyor mezoni:** 10 ta o'zbekcha gapning kamida 8 tasi to'g'ri transkript qilinadi; javob ovozi tushunarli va 3 soniyada boshlanadi.

### 9.10. Ishni qurilmadan qurilmaga ko'chirish
- Har sessiya `state_json` saqlaydi: `{"open_file_id":31,"draft":"...","last_action":"doc_edit"}`.
- Windows ochilganda `GET /sessions?limit=1` → "Telefonda 'Shartnoma' suhbati bor. Davom etamizmi?" → `POST /sessions/{id}/handoff` (boshqa qurilmalarga WS `session_switched` yuboriladi).
- WS orqali real vaqt sinxron: bir qurilmada yuborilgan xabar ikkinchisida 1 soniyada ko'rinadi.
- Fayllar backendda — ikkala qurilma bir xil `file_id`/versiyani ochadi.
**Tayyor mezoni:** telefondan xabar → kompyuterda 1 s ichida; kompyuterda hujjat tahriri → telefonda yangi versiya.

### 9.11. Yagona shaxsiyat
- Ism, ohang, til qoidalari faqat `persona.py`. Ilova nomi, ikonka, salomlashish matni ham shundan olinadi (`YUNA_DISPLAY_NAME`).
- TTS ovozi bitta (`uz-UZ-MadinaNeural`) — uch qurilmada bir xil ovoz.
- Test: bir xil savol uchta kanalda yuboriladi — javob uslubi bir xil bo'lishi kerak.

---

## 10. QURILISH BOSQICHLARI

Har bosqich mustaqil "ishlaydigan" holat beradi. Bosqich tugamaguncha keyingisiga o'tilmaydi. Har bosqich oxirida agent **hisobot** yozadi (10.7 formatida).

### 10.1. 1-bosqich — Poydevor (3–4 kun)
- [ ] Monorepo: `backend/` skelet, `requirements.txt`, `.env.example`, `.gitignore`
- [ ] `config.py`, `db.py`, `main.py` — `/health` ishlaydi
- [ ] Alembic: 6-bo'limdagi to'liq sxema migratsiyasi
- [ ] Auth: register, login, refresh (rotatsiya), logout, `get_current_user`
- [ ] `persona.py` + `ai_service.py` + `POST /chat` (actionsiz, faqat matn)
- [ ] `sessions`/`messages` saqlanadi va qaytariladi
- [ ] pytest: auth oqimi, chat mock bilan, izolyatsiya testi (user A user B'niki ko'rmaydi)
- [ ] Deploy: Render + Neon, HTTPS, `/health` ochiq

**Tayyor mezoni:** `curl` bilan register → login → chat → javob olish ishlaydi; boshqa userning sessiyasiga kirish 403 qaytaradi; Render'dagi URL ishlaydi.

### 10.2. 2-bosqich — Mijozlar (4–5 kun)
- [ ] Telegram bot: webhook, `/start`, auto/manual rejim, xotira, rate limit
- [ ] Windows: login oynasi + chat oynasi (PySide6), token `keyring`da
- [ ] Android: login + chat ekrani (Compose + Retrofit), token `EncryptedSharedPreferences`da
- [ ] Ikkala mijozda: sessiyalar ro'yxati, kod bloklari, xato holatlari

**Tayyor mezoni:** uchala kanaldan bitta sessiya davom etadi; Telegram auto rejimda javob beradi; APK va `.exe` o'z qurilmasida ishlaydi.

### 10.3. 3-bosqich — AI imkoniyatlar (5–7 kun)
- [ ] Rasm tushuntirish (9.2) + siqish
- [ ] Intent tizimi (9.4/9.6/9.8 uchun) — `actions` bajarilishi
- [ ] Eslatmalar + APScheduler + FCM push (9.4)
- [ ] Oziq-ovqat hisobi (9.6)
- [ ] Kundalik maslahat jobi (9.5)
- [ ] Kod rejimi (9.3)

**Tayyor mezoni:** "ertaga 9 da dori eslat" → 09:00 da push keladi; rasm yuborilsa tushuntiriladi; "1 kosa osh" → bazada yozuv; ertalab maslahat keladi.

### 10.4. 4-bosqich — Hujjatlar (3–4 kun)
- [ ] `docx_service`: o'qish, indekslash, JSON farq, qo'llash, versiyalash
- [ ] `POST /docs/upload|edit`, `GET /docs/{id}/download` (imzolangan havola)
- [ ] Fon vazifasi + `doc_ready` WS/push
- [ ] Uch kanalda yuklash/tahrirlash/yuklab olish oqimi

**Tayyor mezoni:** 3 xil hujjat tahrirlanadi, formatlash saqlanadi, versiya 2 olinadi, asl fayl joyida qoladi.

### 10.5. 5-bosqich — Ovoz va qurilma boshqaruvi (5–7 kun)
- [ ] `stt_service` (Gemini + Google zaxira), `tts_service` (edge-tts)
- [ ] `POST /voice/chat`, audio saqlash, kesh
- [ ] APK: mikrofon, ovozli javob ijrosi, ilovalar sinxroni, `open_app`, AccessibilityService (whitelist)
- [ ] WebSocket: sinxron, buyruqlar, `ack`
- [ ] Sessiyani qurilmalar orasida ko'chirish (9.10)

**Tayyor mezoni:** ovozli savol → ovozli javob < 4 s; "Telegramni och" ishlaydi; telefondan boshlangan suhbat kompyuterda davom etadi.

### 10.6. 6-bosqich — Sayqal va chiqarish (3–4 kun)
- [ ] Rate limit (foydalanuvchi 60/min, AI 10/min), `Retry-After`
- [ ] Strukturali loglar (`request_id`, `user_id`, davomiylik), Sentry (ixtiyoriy)
- [ ] Xavfsizlik: 12-bo'lim checklist to'liq
- [ ] Testlar: kamida auth, chat, reminders, food, docs uchun; CI (GitHub Actions)
- [ ] APK release (imzolangan), Windows `.exe` (PyInstaller)
- [ ] `README.md`: o'rnatish, `.env`, migratsiya, ishga tushirish

**Tayyor mezoni:** yangi odam README bo'yicha 30 daqiqada loyihani ishga tushiradi; CI yashil; ikkala installer quriladi.

### 10.7. Agent hisobot formati (har bosqich oxirida)

```markdown
## Bosqich N — hisobot
**Nima qildim:** (3-5 punkt)
**Qanday tekshirdim:** (buyruqlar + natijalar)
**Ishlaydigan demo:** (qadamlar yoki curl misoli)
**Muammo/cheklov:** (bo'lsa)
**Keyingi qadam:** (1 jumla)
```

---

## 11. SINOV STRATEGIYASI

| Daraja | Nima tekshiriladi | Vosita | Qachon |
|---|---|---|---|
| Unit | `intents` (JSON→action), `docx_service` farqi, vaqt hisobi | pytest | har funksiya bilan |
| Integration | endpointlar + baza (test DB) | pytest + httpx AsyncClient | bosqich oxirida |
| AI mock | AI javoblari qaytariladi (haqiqiy chaqiruv yo'q) | fixture | har testda |
| Qo'lda | 3 kanal, real qurilma | checklist | bosqich oxirida |
| Yuklama | 50 parallel chat | locust (ixtiyoriy) | 6-bosqich |

**Qoida:** CI'da AI'ga haqiqiy so'rov yuborilmaydi (xarajat + beqarorlik). `AI_MOCK=true` bo'lsa `ai_service` qayd etilgan javoblarni qaytaradi.

**Qo'lda tekshirish ro'yxati (har bosqichda takrorlanadi):**
1. Yangi user ro'yxatdan o'tadi → chat ishlaydi
2. Boshqa user tokeni bilan begona sessiyaga kirish → 403
3. Internet uziladi → mijoz tushunarli xato ko'rsatadi, qayta urinish ishlaydi
4. Token muddati tugaydi → avtomatik refresh, foydalanuvchi sezmaydi
5. Uch kanalda bir xil savol → bir xil uslubdagi javob

---

## 12. XAVFSIZLIK

- [ ] Barcha kalitlar faqat backend `.env`; APK/Windows kodida **hech qanday** kalit yo'q (grep bilan tekshiriladi)
- [ ] `.env`, `*.keystore`, `serviceAccount.json` `.gitignore` da
- [ ] Parollar argon2id; JWT access 15 daq, refresh 30 kun + rotatsiya + bekor qilish
- [ ] Har so'rovda `user_id` tokendan; barcha SQL'da `WHERE user_id=...`
- [ ] Yuklash: MIME + hajm tekshiruvi, fayl nomi tasodifiy (original nom faqat bazada), antivirus skani (ixtiyoriy, ClamAV)
- [ ] Imzolangan yuklash havolalari (15 daqiqa amal qiladi) — to'g'ridan-to'g'ri bucket ochiq emas
- [ ] Telegram webhook: secret yo'l + sarlavha tekshiruvi
- [ ] Qurilma buyruqlari: whitelist (`open_app`, `open_url`, `notify`, `ping`), har biri `device_commands` da jurnalga yoziladi
- [ ] Rate limit va `Retry-After`; AI xarajatini cheklash (user/kun limiti)
- [ ] Xato javoblarida stack trace va ichki yo'llar ko'rsatilmaydi
- [ ] CORS: faqat kerakli originlar; mobil uchun `null`

---

## 13. DEPLOY

### 13.1. Lokal ishga tushirish (README uchun asos)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # kalitlarni to'ldiring
docker run --name yuna-pg -e POSTGRES_PASSWORD=pg -e POSTGRES_DB=yuna -p 5432:5432 -d postgres:16
alembic upgrade head
uvicorn app.main:app --reload --port 8000
# tekshirish: http://localhost:8000/health  va  /docs (Swagger)
```

### 13.2. Render + Neon

1. Neon'da loyiha → `DATABASE_URL` (asyncpg drayveri bilan: `postgresql+asyncpg://...`)
2. Render → Web Service → repo, root `backend/`, build: `pip install -r requirements.txt`, start: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Environment: 5-bo'limdagi barcha o'zgaruvchilar (kalitlar Render panelida, repo'da emas)
4. Health check path: `/health`
5. Deploydan keyin Telegram webhook: `curl "https://api.telegram.org/bot$TOKEN/setWebhook?url=https://APP/telegram/webhook/$SECRET&secret_token=$SECRET"`
6. **Eslatma:** Render bepul tarifi 15 daqiqa harakatsizlikdan keyin uxlaydi → scheduler uchun `uptime ping` yoki pulli tarif kerak. Buni 4-bosqichda hal qilish: cron-job.org dan har 10 daqiqada `/health` chaqiruvi.

### 13.3. APK va EXE

```bash
# Windows
cd windows && pyinstaller --noconsole --onefile --name Yuna main.py
# APK
cd android && ./gradlew assembleRelease        # imzolash: keystore (gitignore'da)
```

---

## 14. XARAJAT VA LIMITLAR

| Xizmat | Bepul limit | Yetadimi |
|---|---|---|
| Neon | 0.5 GB, 1 loyiha | Ha (shaxsiy foydalanish) |
| Render | 750 soat/oy, uxlaydi | Demo uchun ha; doimiy ish uchun $7/oy |
| OpenRouter bepul modellari | daqiqasiga ~20, kuniga ~50 so'rov | Ha; limitga tushsa router zanjirdagi keyingi modelga o'tadi |
| Cloudflare R2 | 10 GB | Ha |
| edge-tts | bepul | Ha |
| FCM | bepul | Ha |

**Xarajatni boshqarish:** AI'ga qisqa kontekst (20 xabar), `max_output_tokens` chegarasi, TTS kesh, rasm siqish, kunlik AI so'rov limiti.

---

## 15. TEXNIK XATARLAR VA YECHIMLAR

| Xatar | Belgisi | Yechim |
|---|---|---|
| Render uxlab qoladi → eslatma kechikadi | push kelmaydi | Cron ping yoki pulli tarif; kechikkan eslatmalar deploydan keyin "o'tkazib yuborilganlar" sifatida yuboriladi (kechikish > 5 daq bo'lsa "kechikdim" izohi bilan) |
| AI limiti/uzilishi | `AI_UNAVAILABLE` | 3 marta qayta urinish (1s, 3s, 9s), keyin foydalanuvchiga aniq xabar |
| STT o'zbekchada xato | noto'g'ri intent | Ikki provayder + "shunday dedingizmi?" tasdiqlash tugmasi |
| Android fonda ilova ochmaydi | buyruq bajarilmaydi | Foreground service + ruxsatlar bo'yicha qo'llanma ekrani |
| docx formatlash buziladi | shrift/o'lcham yo'qoladi | Run darajasida almashtirish + 3 ta test hujjat |
| WS uzilib qoladi | xabar kechikadi | Avtomatik qayta ulanish + `subscribe`dan keyin to'liq sinxron |
| Bitta user ma'lumotini boshqasi ko'radi | xavfsizlik | Har query'da `user_id`; integration testda majburiy tekshiruv |
| Token o'g'irlanishi | — | Qisqa access TTL, refresh rotatsiyasi, qurilma bo'yicha bekor qilish |

---

## 16. KEYINGI VERSIYA (v2 — hozir qilinmaydi)

- "Hey Yuna" uyg'otuvchi so'z (Android: `Porcupine` yoki `Vosk`)
- Offline kesh (Room/SQLite) va navbatga qo'yilgan xabarlar
- Guruhli Telegram rejimi va bir nechta operator
- Windows'da ekranni ko'rish (vision bilan "ekranimda nima bor?")
- Haftalik hisobot (ovqat, eslatmalar, odatlar) — chiroyli grafik
- Ko'p tilli interfeys (ru/en)

---

## 17. AGENT UCHUN ISHLASH QOIDALARI

1. **Bitta bosqich — bitta yaxlit o'zgarish.** Bosqich ichida mayda commitlar, oxirida bitta yig'ma commit.
2. **Har fayl to'liq yoziladi.** "Bu yerga kodingizni qo'shing" tipidagi bo'shliq qoldirilmaydi.
3. **Ishlaydigan holat saqlanadi.** Har commitdan keyin `uvicorn` ishga tushadi va `/health` javob beradi.
4. **Kalit so'ralmaydi.** `.env.example` to'ldiriladi; haqiqiy kalitlarni inson qo'yadi. Kalit bo'lmasa funksiya "sozlanmagan" deb aniq xato beradi, ilova qulamaydi.
5. **Har yangi funksiyaga kamida 1 test.** AI chaqiruvi mock.
6. **Izohlar, loglar, foydalanuvchiga ko'rinadigan matnlar — o'zbek tilida.** O'zgaruvchi/funksiya nomlari ingliz tilida.
7. **Tushunmagan joyda taxmin qilmaydi** — bitta qisqa savol beradi va to'xtaydi.
8. **Bosqich oxirida hisobot** (10.7 formatida) + `README.md` yangilanadi.

### Git commit formati
```
feat(auth): JWT login va refresh rotatsiyasi
fix(reminders): vaqt zonasi hisobi tuzatildi
docs(readme): ishga tushirish qadamlari
```

---

## 18. LUG'AT (terminal bo'lmagan o'quvchi uchun)

| Atama | Sodda izoh |
|---|---|
| Backend | Serverdagi dastur — hamma qaror shu yerda qabul qilinadi |
| Yupqa mijoz | Faqat ko'rsatadigan va serverga so'rov yuboradigan ilova |
| Endpoint | Serverdagi bitta eshik (masalan `/chat`) |
| WebSocket | Ikki tomonlama jonli aloqa kanali |
| Migratsiya | Bazadagi jadvallarni o'zgartirish qadami |
| Intent / action | AI tushungan amal: "eslatma yarat", "ovqat yoz" |
| STT / TTS | Ovoz→matn / matn→ovoz |
| FCM | Google'ning push xabar xizmati |
| Scheduler | Vaqti kelganda ishni bajaruvchi taymer |
| Rate limit | "Juda ko'p so'rov" himoyasi |
| Versiyalash | Har tahrirdan keyin eski nusxani saqlab, yangisini yaratish |

---

## 19. TEKSHIRUV VARAQASI (chop etib yoniga qo'yish uchun)

```
[ ] 1-bosqich: register → login → chat → deploy     (sana: ____)
[ ] 2-bosqich: Telegram + Windows + APK chat        (sana: ____)
[ ] 3-bosqich: rasm, eslatma, ovqat, maslahat, kod  (sana: ____)
[ ] 4-bosqich: docx tahrirlash + versiya            (sana: ____)
[ ] 5-bosqich: ovoz, ilova ochish, qurilma sinxroni (sana: ____)
[ ] 6-bosqich: xavfsizlik, testlar, APK/EXE release (sana: ____)
```

**Tamom. Har bosqichdan keyin shu varaqni belgilang — reja shu bilan boshqariladi.**
