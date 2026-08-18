from pydantic import BaseModel, UUID4
from typing import Optional
from ..models.workspace import WorkspaceRole

class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None

class WorkspaceOut(BaseModel):
    id: UUID4
    name: str
    description: Optional[str]
    owner_id: UUID4

class WorkspaceMemberAdd(BaseModel):
    user_id: UUID4
    role: WorkspaceRole