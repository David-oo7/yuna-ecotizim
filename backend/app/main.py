"""Y.U.N.A backend — kirish nuqtasi.

Ishga tushirish: uvicorn app.main:app --reload --port 8000
Hujjatlar:      http://localhost:8000/docs
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app import __version__
from app.api.v1 import api_router
from app.config import settings
from app.db import SessionLocal, engine, init_models
from app.models import User
from app.security import TokenError, decode_token
from app.services import ws_manager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s | %(message)s"
)
logger = logging.getLogger("yuna")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.auto_migrate:
        await init_models()
    if not settings.is_test:
        from app.scheduler.jobs import start_scheduler, stop_scheduler

        start_scheduler()
        yield
        stop_scheduler()
    else:
        yield


app = FastAPI(
    title="Y.U.N.A API",
    version=__version__,
    description="Yagona ekotizim backend: chat, eslatma, ovqat, hujjat, ovoz, qurilmalar.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_env == "dev" else [],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------- xato formati ----------------
@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        body = {"error": detail}
    else:
        body = {"error": {"code": "ERROR", "message": str(detail), "field": None}}
    return JSONResponse(status_code=exc.status_code, content=body, headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    first = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(p) for p in first.get("loc", [])[1:]) or None
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION",
                "message": first.get("msg", "Ma'lumot noto'g'ri."),
                "field": field,
            }
        },
    )


app.include_router(api_router, prefix="/api/v1")


# ---------------- health ----------------
@app.get("/health", tags=["health"])
async def health() -> dict:
    db_ok = True
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:  # pragma: no cover
        db_ok = False
    return {
        "ok": db_ok,
        "db": db_ok,
        "ai": settings.ai_enabled,
        "version": __version__,
    }


# ---------------- WebSocket ----------------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = "") -> None:
    try:
        payload = decode_token(token, "access")
    except TokenError:
        await websocket.close(code=4401)
        return

    user_id = int(payload["sub"])
    async with SessionLocal() as db:
        user = await db.get(User, user_id)
        if user is None:
            await websocket.close(code=4401)
            return

    await ws_manager.manager.connect(user_id, websocket)
    await websocket.send_json({"type": "ready", "user_id": user_id})

    try:
        while True:
            data = await websocket.receive_json()
            kind = data.get("type")
            if kind == "ping":
                await websocket.send_json({"type": "pong"})
            elif kind == "subscribe":
                await websocket.send_json(
                    {"type": "subscribed", "session_id": data.get("session_id")}
                )
            elif kind == "ack":
                async with SessionLocal() as db:
                    from app.models import DeviceCommand

                    command = await db.get(DeviceCommand, int(data.get("command_id") or 0))
                    if command and command.user_id == user_id:
                        command.status = "done" if data.get("status") == "done" else "failed"
                        command.result = data.get("result") or {}
                        await db.commit()
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.manager.disconnect(user_id, websocket)
