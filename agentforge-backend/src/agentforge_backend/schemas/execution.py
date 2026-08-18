from pydantic import BaseModel, UUID4
from typing import Optional, Dict
from datetime import datetime
from ..models.execution import ExecutionStatus

class ExecutionStart(BaseModel):
    agent_id: UUID4
    task_id: Optional[UUID4] = None
    input: Dict

class ExecutionOut(BaseModel):
    id: UUID4
    status: ExecutionStatus
    input: Dict
    output: Optional[Dict]
    error: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    retry_count: int
    agent_id: UUID4
    task_id: Optional[UUID4]