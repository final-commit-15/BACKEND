from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from ..config.settings import settings


def get_client_ip(request: Request) -> str:
    """Get client IP address, considering proxies."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(
    key_func=get_client_ip,
    default_limits=[settings.RATE_LIMIT_DEFAULT] if settings.RATE_LIMIT_ENABLED else [],
    storage_uri=settings.REDIS_URL,
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Custom rate limit exceeded handler."""
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": {
                "code": "rate_limit_exceeded",
                "message": f"Rate limit exceeded: {exc.detail}",
            },
        },
        headers={"Retry-After": str(exc.retry_after or 60)},
    )


def get_limiter() -> Limiter:
    """Get the limiter instance."""
    return limiter