from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ...db.session import get_db
from ...services.analytics_service import AnalyticsService
from ...middleware.auth import get_current_user_id

router = APIRouter(tags=["analytics"])

@router.get("/overview")
async def get_overview(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    return await AnalyticsService.get_overview(db, current_user_id)

@router.get("/agents/{agent_id}")
async def get_agent_stats(
    agent_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    return await AnalyticsService.get_agent_stats(db, agent_id, current_user_id)

@router.get("/executions")
async def execution_trend(
    range: str = Query("7d"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await AnalyticsService.execution_activity(
        db, range, current_user_id
    )

@router.get("/agents")
async def agent_usage(
    range: str = Query("7d"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await AnalyticsService.agent_usage(
        db, range, current_user_id
    )

@router.get("/tasks")
async def tasks_over_time(
    range: str = Query("7d"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await AnalyticsService.tasks_over_time(
        db, range, current_user_id
    )


@router.get("/performance")
async def performance(
    range: str = Query("7d"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await AnalyticsService.agent_performance(
        db, range, current_user_id
    )