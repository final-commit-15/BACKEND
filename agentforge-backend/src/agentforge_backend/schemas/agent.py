from pydantic import BaseModel, UUID4
from typing import Optional, Dict, List

class AgentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    agent_type: str
    system_prompt: Optional[str] = None
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    tools: List[str] = []
    permissions: Dict = {}
    memory: Dict = {}
    execution_limits: Dict = {}
    timeout_seconds: int = 60
    retry_policy: Dict = {"max_retries": 3}
    project_id: Optional[UUID4] = None

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    tools: Optional[List[str]] = None
    permissions: Optional[Dict] = None
    memory: Optional[Dict] = None
    execution_limits: Optional[Dict] = None
    timeout_seconds: Optional[int] = None
    retry_policy: Optional[Dict] = None
    is_active: Optional[bool] = None

class AgentOut(BaseModel):
    id: UUID4
    name: str
    description: Optional[str]
    agent_type: str
    model: str
    is_active: bool
    owner_id: UUID4
    project_id: Optional[UUID4]