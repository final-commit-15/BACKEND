from pydantic import BaseModel, UUID4
from datetime import datetime

class NotificationOut(BaseModel):
    id: UUID4
    type: str
    title: str
    message: str
    is_read: bool
    created_at: datetime