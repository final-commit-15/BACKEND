import asyncio
import logging
from contextlib import asynccontextmanager

import asyncpg
import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config.settings import settings
from .utils.logging import setup_logging
from .api.v1 import router as api_router
from .db.redis import get_redis_client, close_redis_client

# Expose redis client for deps
redis_client = None

setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    # Database connection is handled per request via dependency
    try:
        redis_client = await get_redis_client()
        logger.info("Redis connection established.")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
    yield
    # Cleanup
    await close_redis_client()
    logger.info("Redis connection closed.")

app = FastAPI(title="AgentForge Backend", version="0.1.0", lifespan=lifespan)

origins = [
    "http://localhost:5173",   # Vite
    "http://127.0.0.1:5173",
    "http://localhost:3000",   # Optional React
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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