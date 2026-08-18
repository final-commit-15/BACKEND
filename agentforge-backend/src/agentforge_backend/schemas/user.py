from pydantic import BaseModel, EmailStr, UUID4
from typing import Optional
from ..models.user import UserRole

class UserOut(BaseModel):
    id: UUID4
    email: EmailStr
    username: str
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool

class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None