"""Redis cache helpers and key patterns (week 2)."""

import json
from typing import Any

from app.core.redis_client import redis_client

# TTL seconds
TTL_TENDERS_ACTIVE = 300       # 5 min
TTL_CATEGORIES = 3600          # 1 hour
TTL_SUPPLIER_RATING = 1800     # 30 min
TTL_USER_SESSION = 900         # 15 min
TTL_BUDGET_ANALYTICS = 86400   # 1 day


def cache_key_tenders_active(page: int, status: str | None) -> str:
    status_part = status or "all"
    return f"tenders:active:page:{page}:status:{status_part}"


def cache_key_categories() -> str:
    return "categories:all"


def cache_key_supplier_rating(supplier_id: int) -> str:
    return f"supplier:rating:{supplier_id}"


def cache_key_session(user_id: int) -> str:
    return f"session:{user_id}"


def cache_get(key: str) -> Any | None:
    value = redis_client.get(key)
    if value is None:
        return None
    return json.loads(value)


def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    redis_client.setex(key, ttl, json.dumps(value, default=str))


def cache_delete(key: str) -> None:
    redis_client.delete(key)


def cache_delete_pattern(pattern: str) -> None:
    keys = redis_client.keys(pattern)
    if keys:
        redis_client.delete(*keys)


def invalidate_tenders_cache() -> None:
    cache_delete_pattern("tenders:active:*")
