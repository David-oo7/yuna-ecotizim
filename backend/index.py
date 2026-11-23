"""Vercel entrypoint.

Vercel'ning Python runtime'i ASGI ilovani `app` nomli o'zgaruvchidan qidiradi.
Loyihaning asosiy FastAPI obyekti `app.main` ichida bo'lgani uchun shu yerda
qayta eksport qilinadi.
"""

from app.main import app

__all__ = ["app"]
