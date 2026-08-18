from pydantic import BaseModel, UUID4, HttpUrl
from typing import Optional, List, Dict

class WebhookCreate(BaseModel):
    name: str
    url: HttpUrl
    secret: str
    events: List[str]
    retry_config: Dict = {"max_retries": 3, "backoff_seconds": 60}
    project_id: Optional[UUID4] = None

class WebhookOut(BaseModel):
    id: UUID4
    name: str
    url: str
    events: List[str]
    is_active: bool
    user_id: UUID4
    project_id: Optional[UUID4]