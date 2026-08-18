from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ...db.session import get_db
from ...services.analytics_service import AnalyticsService
from ...middleware.auth import get_current_user_id

router = APIRouter(prefix="/analytics", tags=["analytics"])

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