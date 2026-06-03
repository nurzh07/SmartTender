from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import get_settings
from app.core.redis_client import redis_client

settings = get_settings()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis IP rate limit: 100 requests per minute (configurable)."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path in ("/health", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{client_ip}"

        try:
            count = redis_client.incr(key)
            if count == 1:
                redis_client.expire(key, settings.RATE_LIMIT_WINDOW_SECONDS)
            if count > settings.RATE_LIMIT_REQUESTS:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Try again later."},
                )
        except Exception:
            pass

        return await call_next(request)
