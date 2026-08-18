from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.task import Task, TaskStatus
from ..schemas.task import TaskCreate, TaskUpdate
from ..utils.exceptions import NotFoundError

class TaskService:
    @staticmethod
    async def create(db: AsyncSession, data: TaskCreate, user_id: str) -> Task:
        task = Task(**data.dict())
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task

    @staticmethod
    async def get_by_id(db: AsyncSession, task_id: str) -> Task | None:
        return await db.get(Task, task_id)

    @staticmethod
    async def list(db: AsyncSession, project_id: str | None = None):
        stmt = select(Task)
        if project_id:
            stmt = stmt.where(Task.project_id == project_id)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def update(db: AsyncSession, task_id: str, data: TaskUpdate) -> Task:
        task = await db.get(Task, task_id)
        if not task:
            raise NotFoundError("Task not found")
        update_data = data.dict(exclude_unset=True)
        for k, v in update_data.items():
            setattr(task, k, v)
        await db.commit()
        await db.refresh(task)
        return task

    @staticmethod
    async def delete(db: AsyncSession, task_id: str) -> bool:
        task = await db.get(Task, task_id)
        if not task:
            return False
        await db.delete(task)
        await db.commit()
        return True