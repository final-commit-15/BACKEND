from pydantic import BaseModel, UUID4
from typing import Optional, List, Dict
from datetime import datetime
from ..models.task import TaskStatus

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: int = 0
    deadline: Optional[datetime] = None
    dependencies: List[UUID4] = []
    assignee_id: Optional[UUID4] = None
    project_id: Optional[UUID4] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[int] = None
    deadline: Optional[datetime] = None
    assignee_id: Optional[UUID4] = None

class TaskOut(BaseModel):
    id: UUID4
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: int
    deadline: Optional[datetime]
    assignee_id: Optional[UUID4]
    project_id: Optional[UUID4]