# Y.U.N.A — yagona ekotizim

Bitta backend atrofida ishlaydigan shaxsiy AI yordamchi: **Android APK**, **Windows ilova**
va **Telegram bot** — hammasi bitta bazadan, bitta shaxsiyatdan (Yuna) foydalanadi.

> To'liq reja va arxitektura: [`YUNA_ekotizim_reja.md`](YUNA_ekotizim_reja.md)

---

## 3 daqiqada ishga tushirish

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -r requirements.txt
cp .env.example .env                                 # GEMINI_API_KEY ni qo'ying (ixtiyoriy)
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Tekshirish:

- API hujjati (Swagger): <http://localhost:8000/docs>
- Salomatlik: <http://localhost:8000/health>

> `.env` da `GEMINI_MOCK=true` bo'lsa AI tarmoqqa chiqmaydi va tayyor (mock) javoblar
> qaytaradi — kalitsiz ham butun oqimni sinash mumkin. Haqiqiy AI uchun
> `GEMINI_API_KEY` ni qo'ying va `GEMINI_MOCK=false` qiling.

---

## Testlar

```bash
cd backend
python -m pytest              # 30 ta test, ~5 s (tarmoqsiz, AI mock)
python scripts/smoke_test.py  # server ishlab turgan holatda jonli 17 ta tekshiruv
```

Nima qoplanadi: auth (register/login/refresh rotatsiyasi), chat va sessiyalar,
foydalanuvchilar izolyatsiyasi, eslatmalar (tabiiy til → vaqt, yetkazish, takrorlanish),
ovqat hisobi, Word tahriri va versiyalash, ovoz (STT/TTS), rasm, qurilma buyruqlari,
rate limit, kundalik maslahat, xato formati.

---

## Nima tayyor

| Bo'lim | Holat |
|---|---|
| Backend skeleti, sozlamalar, baza (12 jadval), Alembic migratsiya | ✅ |
| Auth: JWT + refresh rotatsiyasi + argon2 + `/me` | ✅ |
| Suhbat: `/chat`, SSE `/chat/stream`, sessiyalar, qurilmalar orasida davom ettirish | ✅ |
| Y.U.N.A shaxsiyati — `app/services/persona.py` (yagona manba) | ✅ |
| Intent tizimi: eslatma, ovqat, ilova ochish (noto'g'ri JSON bajarilmaydi) | ✅ |
| Eslatmalar: tabiiy til → vaqt, scheduler, takrorlanish, push/WS/Telegram | ✅ |
| Ovqat hisobi: matn → taomlar → kkal/oqsil/yog'/uglevod, kunlik jami | ✅ |
| Kundalik maslahat (kuniga 1 ta, takrorlanmaydi) | ✅ |
| Word: yuklash → AI tahriri → yangi versiya → yuklab olish | ✅ |
| Ovoz: STT (Gemini, zaxira reja), TTS (edge-tts `uz-UZ-MadinaNeural`), `/voice/chat` | ✅ |
| Rasm tushuntirish (siqish + vision) | ✅ |
| Qurilmalar: ro'yxatga olish, ilovalar sinxroni, buyruq + ack | ✅ |
| WebSocket: real vaqt sinxron, buyruqlar, eslatma/maslahat yetkazish | ✅ |
| Telegram: webhook, auto/manual rejim, tasdiqlash tugmalari, rate limit | ✅ kod tayyor, token kerak |
| Windows ilova (PySide6): login, chat, kod bloklari, WS | ✅ kod tayyor, GUI sinalmagan |
| Android (Kotlin + Compose): login, chat, ovoz, ilova ochish, FCM | ✅ kod tayyor, APK qurilmagan |

---

## Tuzilma

```
backend/
  app/
    main.py              FastAPI, /health, /ws
    config.py db.py models.py schemas.py security.py deps.py ratelimit.py
    api/v1/              auth, chat, sessions, reminders, food, advice, docs, voice, vision, devices, telegram
    services/            ai_service, persona, intents, chat_service, reminder_service,
                         food_service, advice_service, docx_service, audio_service,
                         storage_service, push_service, ws_manager, telegram_service
    scheduler/jobs.py    eslatmalar (30 s), maslahat (60 s)
  alembic/               migratsiyalar
  tests/                 30 ta test
  scripts/smoke_test.py  jonli uchdan-uchga tekshiruv
windows/                 PySide6 ilova (api.py, main.py)
android/                 Kotlin + Jetpack Compose loyihasi
YUNA_ekotizim_reja.md    to'liq reja
```

---

## Asosiy endpointlar

```
POST /api/v1/auth/register|login|refresh|logout     GET|PATCH /api/v1/me
POST /api/v1/chat            POST /api/v1/chat/stream (SSE)
GET  /api/v1/sessions        POST /api/v1/sessions/{id}/handoff
POST /api/v1/reminders       GET/PATCH/DELETE /api/v1/reminders/{id}
POST /api/v1/food/log        GET /api/v1/food/summary?date=
GET  /api/v1/advice/today
POST /api/v1/docs/upload|edit    GET /api/v1/docs/{id}/download
POST /api/v1/voice/stt|tts|chat
POST /api/v1/vision/explain
POST /api/v1/devices/register|apps/sync|command    POST /api/v1/devices/commands/{id}/ack
POST /api/v1/telegram/webhook/{secret}
WS   /ws?token=<access_token>
GET  /health
```

Xato formati (barcha endpointlarda bir xil):

```json
{ "error": { "code": "VALIDATION", "message": "text bo'sh bo'lmasin", "field": "text" } }
```

---

## Windows ilova

```bash
cd windows
pip install -r requirements.txt
python main.py
```

Backend manzilini o'zgartirish: `set YUNA_API_URL=https://sizning-server.onrender.com`

## Android

1. Android Studio → `android/` papkasini ochish
2. `app/build.gradle.kts` dagi `API_URL` ni server manziliga o'zgartirish
   (emulyator uchun `http://10.0.2.2:8000`, real qurilma uchun HTTPS manzil)
3. Push kerak bo'lsa: Firebase loyihasi → `google-services.json` ni `app/` ga qo'ying va
   `build.gradle.kts` ga `com.google.gms.google-services` plaginini qo'shing
4. `./gradlew assembleDebug` yoki Android Studio'dan Run

---

## Render'ga chiqarish (Web Service)

Repo: <https://github.com/David-oo7/yuna-ecotizim> (backend shu repo ichida, `backend/` papkasida).

1. **Baza:** Render → **New → Postgres** → yaratilgach **Internal Database URL** ni nusxalang.
   Kod `postgres://` va `postgresql://` manzillarini o'zi `postgresql+asyncpg://` ga o'giradi
   (`app/config.py`), shuning uchun URL'ni o'zgartirmasdan qo'yaverasiz.
2. **Web Service:** Render → New → Web Service → repo'ni tanlang, keyin:

   | Sozlama | Qiymat |
   |---|---|
   | Language | Python 3 |
   | **Root Directory** | `backend` |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1` |
   | Health Check Path | `/health` |

   > `--workers 1` muhim: scheduler (eslatmalar) har bir worker'da alohida ishlaydi, bir nechta
   > worker eslatmalarni takrorlab yuboradi.
3. **Environment** (Render → Environment):

   ```
   APP_ENV=prod
   APP_SECRET_KEY=<quyidagi buyruq bilan yarating>
   APP_BASE_URL=https://<servis-nomi>.onrender.com
   DATABASE_URL=<Render Postgres'dagi Internal Database URL>
   AUTO_MIGRATE=true
   GEMINI_API_KEY=<kalitingiz>      # bo'sh qolsa chat AI javob bermaydi
   GEMINI_MOCK=false
   STORAGE_LOCAL_DIR=/var/data/storage
   STORAGE_DRIVER=local
   ```

   Maxfiy kalitni yaratish:

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

4. **Fayllar (Word/ovoz):** Render diski vaqtinchalik — qayta deploy'da fayllar o'chadi. Ikki yo'l:
   - **Render Disk** (pulli tarif): Add Disk → Mount Path `/var/data` → `STORAGE_LOCAL_DIR=/var/data/storage`
   - **Cloudflare R2** (bepul): `STORAGE_DRIVER=r2` + `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`,
     `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`
5. Deploy tugagach tekshirish: `https://<servis>.onrender.com/health` → `{"ok": true, ...}`
6. Mijozlarni yangilash:
   - Android: `android/app/build.gradle.kts` dagi `API_URL` → `https://<servis>.onrender.com`
     (HTTPS bo'lgani uchun cleartext shart emas)
   - Windows: `set YUNA_API_URL=https://<servis>.onrender.com`
7. Telegram webhook:
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<app>/api/v1/telegram/webhook/<SECRET>&secret_token=<SECRET>"
   ```
8. **Diqqat:** Render bepul tarifi 15 daqiqa harakatsizlikdan keyin uxlaydi — eslatmalar
   kechikmasligi uchun cron-job.org dan har 10 daqiqada `/health` chaqiring yoki pulli tarif oling.

---

## Xavfsizlik qoidalari

- Kalitlar faqat `backend/.env` da; APK/Windows kodida hech qanday kalit yo'q
- Har so'rovda `user_id` tokendan olinadi; barcha so'rovlar `user_id` bo'yicha cheklangan
  (testlar bilan tekshirilgan: `tests/test_chat.py::test_isolation_between_users`)
- Parollar argon2, access token 15 daqiqa, refresh 30 kun + rotatsiya
- Yuklash: tur va hajm cheklovi; yuklab olish havolalari taxmin qilib bo'lmaydigan nom bilan
- Qurilma buyruqlari whitelist ichida (`open_app`, `open_url`, `notify`, `ping`)

---

## Keyingi qadamlar (reja bo'yicha)

1. `GEMINI_API_KEY` qo'yish va real AI bilan 10 ta savolda aniqlikni tekshirish
2. Neon + Render'ga deploy, `alembic upgrade head`
3. Telegram tokenini qo'yish va botni ulash
4. `uz-UZ` STT sifatini 10 ta ovozli namunada o'lchash
5. APK release keystore va Windows `.exe` (PyInstaller) yig'ish
6. FCM `google-services.json` + service account JSON qo'shish

Batafsil: `YUNA_ekotizim_reja.md` 10-bo'lim (bosqichlar) va 19-bo'lim (tekshiruv varaqasi).
