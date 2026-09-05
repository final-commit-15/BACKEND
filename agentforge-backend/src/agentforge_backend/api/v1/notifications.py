from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ...db.session import get_db
from ...services.notification_service import NotificationService
from ...middleware.auth import get_current_user_id
from ...schemas.notification import NotificationOut

router = APIRouter(tags=["notifications"])

@router.get("/", response_model=List[NotificationOut])
async def list_notifications(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    return await NotificationService.list_by_user(db, current_user_id)

@router.patch("/{notification_id}/read", response_model=NotificationOut)
async def mark_read(
    notification_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    return await NotificationService.mark_read(db, notification_id, current_user_id)