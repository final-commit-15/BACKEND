from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

from ..deps import get_current_user, get_db
from ...models.user import User
from ...services.tools import ToolsService

router = APIRouter()

class ToolBase(BaseModel):
    name: str
    category: str
    description: str
    version: str = "1.0.0"

class ToolCreate(ToolBase):
    pass

class ToolUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    enabled: Optional[bool] = None

class Tool(ToolBase):
    id: UUID
    enabled: bool

@router.get("/", response_model=List[Tool])
async def list_tools(
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    service = ToolsService(db)
    tools = await service.get_all_tools(current_user.active_workspace_id)
    return [Tool(**t) for t in tools]

@router.post("/", response_model=Tool, status_code=201)
async def register_tool(
    tool_in: ToolCreate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    service = ToolsService(db)
    tool = await service.create_tool(tool_in.dict(), current_user.active_workspace_id)
    return Tool(**tool)

@router.put("/{tool_id}", response_model=Tool)
async def update_tool(
    tool_id: UUID,
    tool_in: ToolUpdate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    service = ToolsService(db)
    updated = await service.update_tool(tool_id, tool_in.dict(exclude_unset=True), current_user.active_workspace_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Tool not found")
    return Tool(**updated)

@router.delete("/{tool_id}", status_code=204)
async def delete_tool(
    tool_id: UUID,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    service = ToolsService(db)
    deleted = await service.delete_tool(tool_id, current_user.active_workspace_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tool not found")