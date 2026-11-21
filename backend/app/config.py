"""Ilova sozlamalari — barcha qiymatlar .env dan o'qiladi."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Umumiy
    app_env: str = "dev"
    app_secret_key: str = "dev-secret-change-me"
    app_base_url: str = "http://localhost:8000"
    auto_migrate: bool = True

    # Baza
    database_url: str = "sqlite+aiosqlite:///./yuna.db"

    # JWT
    jwt_algorithm: str = "HS256"
    access_token_ttl_min: int = 15
    refresh_token_ttl_days: int = 30

    # AI (OpenRouter — bepul modellar, vazifaga qarab avtomatik tanlanadi)
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    ai_mock: bool = False
    # Modelni qo'lda almashtirish: bo'sh bo'lsa avtomatik zanjir ishlaydi.
    ai_model_chat: str = ""
    ai_model_code: str = ""
    ai_model_vision: str = ""
    ai_model_doc: str = ""
    ai_model_audio: str = ""

    # Telegram
    telegram_bot_token: str = ""
    telegram_webhook_secret: str = "devsecret"

    # Fayllar
    storage_driver: str = "local"
    storage_local_dir: str = "./storage"
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket: str = "yuna-files"
    upload_max_mb: int = 20

    # Push
    fcm_credentials_json: str = ""

    @field_validator("database_url")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        """Render/Heroku beradigan URL'ni async drayvеrga moslaydi.

        postgres://...      -> postgresql+asyncpg://...
        postgresql://...    -> postgresql+asyncpg://...
        ?sslmode=require    -> ?ssl=require  (asyncpg buni kutadi)
        """
        value = value.strip()
        if value.startswith("postgres://"):
            value = "postgresql+asyncpg://" + value[len("postgres://") :]
        elif value.startswith("postgresql://"):
            value = "postgresql+asyncpg://" + value[len("postgresql://") :]
        if "sslmode=" in value:
            value = value.replace("sslmode=", "ssl=")
        return value

    @property
    def is_test(self) -> bool:
        return self.app_env == "test"

    @property
    def ai_enabled(self) -> bool:
        return bool(self.openrouter_api_key) or self.ai_mock


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
