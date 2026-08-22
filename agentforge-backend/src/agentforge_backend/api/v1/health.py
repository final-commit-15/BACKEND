from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Literal
from sqlalchemy import text
from redis.asyncio import Redis

from ..deps import get_db, get_redis
from ...config.settings import settings

router = APIRouter()

class HealthResponse(BaseModel):
    status: Literal["healthy", "unhealthy"]
    database: Literal["connected", "disconnected"]
    redis: Literal["connected", "disconnected"]
    celery: Literal["running", "stopped"]   # placeholder – you can check Celery if needed
    version: str

@router.get("/", response_model=HealthResponse)
async def health_check(
    db=Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    db_ok = True
    redis_ok = True

    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    try:
        await redis.ping()
    except Exception:
        redis_ok = False

    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database": "connected" if db_ok else "disconnected",
        "redis": "connected" if redis_ok else "disconnected",
        "celery": "running",
        "version": getattr(settings, "APP_VERSION", "1.0.0"),
    }

@router.get("/live")
async def liveness():
    return {"status": "alive"}

@router.get("/ready")
async def readiness(db=Depends(get_db), redis: Redis = Depends(get_redis)):
    # Similar to health but returns 200 if dependencies are ready
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    redis_ok = False
    try:
        await redis.ping()
        redis_ok = True
    except Exception:
        pass

    if not (db_ok and redis_ok):
        return {"status": "not ready", "database": db_ok, "redis": redis_ok}, 503
    return {"status": "ready"}