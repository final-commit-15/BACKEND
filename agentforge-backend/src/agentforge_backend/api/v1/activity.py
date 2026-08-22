from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ..deps import get_current_user, get_db
from ...models.user import User
from ...services.activity import ActivityService

router = APIRouter()

class ActivityItem(BaseModel):
    id: UUID
    type: str
    action: str
    user: str
    created_at: str
    extra_data: Optional[dict] = None

class ActivityListResponse(BaseModel):
    page: int
    limit: int
    total: int
    items: List[ActivityItem]

@router.get("/", response_model=ActivityListResponse)
async def list_activity(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    service = ActivityService(db)
    data = await service.get_activity_log(current_user.active_workspace_id, page, limit)
    return ActivityListResponse(**data)

@router.get("/{activity_id}", response_model=ActivityItem)
async def get_activity_detail(
    activity_id: UUID,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    service = ActivityService(db)
    item = await service.get_activity_by_id(activity_id, current_user.active_workspace_id)
    if not item:
        raise HTTPException(status_code=404, detail="Activity not found")
    return ActivityItem(**item)