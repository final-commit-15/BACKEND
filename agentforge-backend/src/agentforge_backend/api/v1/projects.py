from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ...db.session import get_db
from ...services.project_service import ProjectService
from ...middleware.auth import get_current_user_id
from ...schemas.project import ProjectCreate, ProjectOut
from ...utils.exceptions import NotFoundError

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    return await ProjectService.create(db, data, current_user_id)

@router.get("/", response_model=List[ProjectOut])
async def list_projects(
    workspace_id: str,
    db: AsyncSession = Depends(get_db)
):
    return await ProjectService.list_by_workspace(db, workspace_id)

@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    project = await ProjectService.get_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project