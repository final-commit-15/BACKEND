from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from ..deps import get_current_user, get_db
from ...models.user import User
from ...services.settings import SettingsService

router = APIRouter()

class SettingsBase(BaseModel):
    theme: str = "dark"
    language: str = "en"
    timezone: str = "Asia/Kolkata"
    notifications: bool = True
    auto_save: bool = True
    default_model: str = "gpt-5"

class SettingsUpdate(SettingsBase):
    pass

class SettingsResponse(SettingsBase):
    workspace_id: UUID

@router.get("/", response_model=SettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    service = SettingsService(db)
    settings = await service.get_workspace_settings(current_user.active_workspace_id)
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return settings

@router.put("/", response_model=SettingsResponse)
async def update_settings(
    settings_in: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    service = SettingsService(db)
    updated = await service.update_workspace_settings(
        current_user.active_workspace_id, settings_in.dict(exclude_unset=True)
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Settings not found")
    return updated

@router.post("/reset", response_model=SettingsResponse)
async def reset_settings(
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    service = SettingsService(db)
    default = SettingsBase().dict()
    reset = await service.update_workspace_settings(current_user.active_workspace_id, default)
    if not reset:
        raise HTTPException(status_code=404, detail="Settings not found")
    return reset