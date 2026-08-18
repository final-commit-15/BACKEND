from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ...db.session import get_db
from ...services.task_service import TaskService
from ...middleware.auth import get_current_user_id
from ...schemas.task import TaskCreate, TaskOut, TaskUpdate, TaskStatus
from ...utils.exceptions import NotFoundError

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: TaskCreate,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    return await TaskService.create(db, data, current_user_id)

@router.get("/", response_model=List[TaskOut])
async def list_tasks(
    project_id: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    return await TaskService.list(db, project_id)

@router.get("/{task_id}", response_model=TaskOut)
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    task = await TaskService.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(task_id: str, data: TaskUpdate, db: AsyncSession = Depends(get_db)):
    return await TaskService.update(db, task_id, data)

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str, db: AsyncSession = Depends(get_db)):
    deleted = await TaskService.delete(db, task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")