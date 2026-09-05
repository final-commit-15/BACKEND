from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from ..config.settings import settings
import logging

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """Get client IP address, considering proxies."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


# Global limiter instance (initialized lazily)
_limiter = None


def _create_limiter(storage_uri: str) -> Limiter:
    """Create a new limiter instance with given storage."""
    return Limiter(
        key_func=get_client_ip,
        default_limits=[settings.RATE_LIMIT_DEFAULT] if settings.RATE_LIMIT_ENABLED else [],
        storage_uri=storage_uri,
    )


def get_limiter() -> Limiter:
    """Get the limiter instance, initializing if needed."""
    global _limiter
    if _limiter is None:
        _limiter = _create_limiter("memory://")
    return _limiter


# Backward compatibility
limiter = get_limiter()


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Custom rate limit exceeded handler."""
    # RateLimitExceeded may not have retry_after attribute, default to 60 seconds
    retry_after = getattr(exc, 'retry_after', None) or 60
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": {
                "code": "rate_limit_exceeded",
                "message": f"Rate limit exceeded: {exc.detail}",
            },
        },
        headers={"Retry-After": str(retry_after)},
    )


def init_rate_limiter():
    """Initialize rate limiter with Redis fallback."""
    global _limiter, limiter
    if not settings.RATE_LIMIT_ENABLED:
        return
    
    # Test Redis connection
    import redis
    try:
        client = redis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
        client.ping()
        logger.info("Rate limiter using Redis storage")
        storage_uri = settings.REDIS_URL
    except Exception:
        logger.warning("Redis unavailable, rate limiter falling back to in-memory storage")
        storage_uri = "memory://"
    
    _limiter = _create_limiter(storage_uri)
    limiter = _limiter


def add_rate_limiter_middleware(app):
    """Add SlowAPI rate limiting middleware to the app."""
    # Initialize limiter first
    init_rate_limiter()
    # Add the middleware
    app.add_middleware(SlowAPIMiddleware)