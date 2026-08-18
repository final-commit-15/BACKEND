import asyncio
import logging
from contextlib import asynccontextmanager

import asyncpg
import redis.asyncio as redis
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .config.settings import settings
from .utils.logging import setup_logging

# ----- Import all API routers (v1) -----
from .api.v1 import (
    auth,
    users,
    agents,
    tasks,
    executions,
    workspaces,
    projects,
)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global state for dependency checks (used in readiness)
db_conn = None
redis_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    global db_conn, redis_client

    try:
        dsn = settings.DATABASE_URL.replace(
            "postgresql+asyncpg://",
            "postgresql://",
            1,
        )
        db_conn = await asyncpg.connect(dsn)
        logger.info("Database connection established.")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")

    try:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
        await redis_client.ping()
        logger.info("Redis connection established.")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")

    yield

    if db_conn:
        await db_conn.close()
        logger.info("Database connection closed.")

    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed.")


# ----- Create FastAPI app -----
app = FastAPI(
    title="AgentForge Backend",
    version="0.1.0",
    lifespan=lifespan,
)

# ----- CORS middleware -----
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- Include all v1 routers -----
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(executions.router, prefix="/api/v1")
app.include_router(workspaces.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")

# ----- Health endpoints -----
@app.get("/health", status_code=status.HTTP_200_OK)
async def health():
    """Basic application health."""
    return {"status": "ok"}


@app.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness():
    """Liveness probe – process is alive."""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    """Readiness probe – checks DB and Redis."""
    checks = {
        "database": False,
        "redis": False,
    }

    overall = True

    try:
        if db_conn is None:
            raise RuntimeError("Database connection is not available")

        await db_conn.fetchrow("SELECT 1")
        checks["database"] = True
    except Exception:
        overall = False

    try:
        if redis_client is None:
            raise RuntimeError("Redis connection is not available")

        await redis_client.ping()
        checks["redis"] = True
    except Exception:
        overall = False

    if not overall:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "checks": checks,
            },
        )

    return {
        "status": "ready",
        "checks": checks,
    }

# ----- Optional root endpoint -----
@app.get("/")
async def root():
    return {"message": "AgentForge Backend is running."}