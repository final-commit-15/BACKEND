from pydantic import BaseModel, UUID4
from typing import Optional, Dict

class IntegrationCreate(BaseModel):
    name: str
    provider: str
    credentials: Dict  # will be encrypted
    config: Dict = {}

class IntegrationOut(BaseModel):
    id: UUID4
    name: str
    provider: str
    is_active: bool
    user_id: UUID4