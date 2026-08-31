from pydantic import BaseModel, EmailStr, ConfigDict, Field
from uuid import UUID
from typing import Optional


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    revoke_all: bool = False


# ---------- Requests ----------
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)


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