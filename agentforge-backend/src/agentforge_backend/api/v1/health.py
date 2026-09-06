from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from typing import Literal, Optional, Dict, Any
from sqlalchemy import text
from redis.asyncio import Redis

from ..deps import get_db, get_redis
from ...config.settings import settings
from ...core.supabase import supabase_health_check
from ...monitoring.metrics import get_metrics

router = APIRouter()


class HealthComponent(BaseModel):
    status: Literal["healthy", "unhealthy", "unknown"]
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    environment: str
    database: HealthComponent
    redis: HealthComponent
    supabase: HealthComponent
    celery: HealthComponent


@router.get("/", response_model=HealthResponse)
async def health_check(
    db=Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    # Check database
    db_healthy = True
    db_error = None
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_healthy = False
        db_error = str(e)

    # Check Redis
    redis_healthy = True
    redis_error = None
    try:
        await redis.ping()
    except Exception as e:
        redis_healthy = False
        redis_error = str(e)

    # Check Supabase
    supabase_results = await supabase_health_check()
    supabase_healthy = all(
        r["status"] == "healthy" for r in supabase_results.values()
    )
    
    # Overall status
    if db_healthy and redis_healthy and supabase_healthy:
        overall_status = "healthy"
    elif db_healthy or redis_healthy or supabase_healthy:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    return HealthResponse(
        status=overall_status,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        database=HealthComponent(
            status="healthy" if db_healthy else "unhealthy",
            error=db_error,
        ),
        redis=HealthComponent(
            status="healthy" if redis_healthy else "unhealthy",
            error=redis_error,
        ),
        supabase=HealthComponent(
            status="healthy" if supabase_healthy else "unhealthy",
            details=supabase_results,
        ),
        celery=HealthComponent(
            status="running",  # Placeholder - add actual Celery check if needed
        ),
    )


@router.get("/live")
async def liveness():
    return {"status": "alive"}


@router.get("/ready")
async def readiness(
    db=Depends(get_db),
    redis: Redis = Depends(get_redis),
):
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

    # Also check Supabase for readiness
    supabase_ok = False
    try:
        supabase_results = await supabase_health_check()
        supabase_ok = all(r["status"] == "healthy" for r in supabase_results.values())
    except Exception:
        pass

    if not (db_ok and redis_ok and supabase_ok):
        return {
            "status": "not ready",
            "database": db_ok,
            "redis": redis_ok,
            "supabase": supabase_ok,
        }, 503

    return {"status": "ready"}


@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    if not settings.METRICS_ENABLED:
        return Response(content="Metrics disabled", status_code=404)
    return get_metrics()