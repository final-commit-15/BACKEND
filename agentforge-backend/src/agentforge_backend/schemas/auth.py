from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID

class RefreshRequest(BaseModel):
    refresh_token: str

# ---------- Requests ----------
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# ---------- Responses ----------
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    full_name: str
    role: str
    is_active: bool
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)