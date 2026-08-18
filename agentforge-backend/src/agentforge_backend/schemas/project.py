from pydantic import BaseModel, UUID4
from typing import Optional

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    workspace_id: UUID4

class ProjectOut(BaseModel):
    id: UUID4
    name: str
    description: Optional[str]
    workspace_id: UUID4