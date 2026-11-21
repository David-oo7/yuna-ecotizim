"""Oddiy in-memory rate limit (bitta jarayon uchun yetarli).

Ko'p instansiyali deployda Redis'ga ko'chiriladi — interfeys o'zgarmaydi.
"""

import time
from collections import defaultdict, deque

from fastapi import Depends

from app.deps import AppError
from app.models import User
from app.deps import get_current_user

_buckets: dict[str, deque[float]] = defaultdict(deque)


def check(key: str, limit: int, window_sec: int = 60) -> bool:
    now = time.monotonic()
    bucket = _buckets[key]
    while bucket and now - bucket[0] > window_sec:
        bucket.popleft()
    if len(bucket) >= limit:
        return False
    bucket.append(now)
    return True


def reset() -> None:
    _buckets.clear()


def ai_limit(user: User = Depends(get_current_user)) -> User:
    if not check(f"ai:{user.id}", limit=10):
        raise AppError(
            429,
            "RATE_LIMITED",
            "Juda ko'p so'rov. Bir daqiqadan keyin urinib ko'ring.",
            headers={"Retry-After": "60"},
        )
    return user
