import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config.settings import settings
from .utils.logging import setup_logging
from .api.v1 import router as api_router
from .db.redis import get_redis_client, close_redis_client
from .middleware.rate_limiter import limiter, rate_limit_exceeded_handler
from .middleware.security_headers import add_security_headers_middleware
from .middleware.request_logging import add_request_logging_middleware

# Expose redis client for deps
redis_client = None

setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    try:
        redis_client = await get_redis_client()
        logger.info("Redis connection established.")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
    yield
    await close_redis_client()
    logger.info("Redis connection closed.")

app = FastAPI(
    title="AgentForge Backend",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# CORS - use settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.cors_allow_methods_list,
    allow_headers=settings.cors_allow_headers_list,
)

# Security headers
add_security_headers_middleware(app)

# Request logging
add_request_logging_middleware(app)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(429, rate_limit_exceeded_handler)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def root_health():
    return {"status": "ok"}

@app.get("/health/live")
async def root_liveness():
    return {"status": "alive"}

@app.get("/health/ready")
async def root_readiness():
    return {"status": "ready"}

@app.get("/")
async def root():
    return {"message": "AgentForge Backend is running."}