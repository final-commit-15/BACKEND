from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ...db.session import get_db
from ...services.workspace_service import WorkspaceService
from ...middleware.auth import get_current_user_id
from ...schemas.workspace import WorkspaceCreate, WorkspaceOut, WorkspaceMemberAdd
from ...utils.exceptions import NotFoundError, PermissionDeniedError

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

@router.post("/", response_model=WorkspaceOut, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    data: WorkspaceCreate,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    return await WorkspaceService.create(db, data, current_user_id)

@router.get("/", response_model=List[WorkspaceOut])
async def list_workspaces(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    return await WorkspaceService.list_by_user(db, current_user_id)

@router.post("/{workspace_id}/members")
async def add_member(
    workspace_id: str,
    data: WorkspaceMemberAdd,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    return await WorkspaceService.add_member(db, workspace_id, data, current_user_id)