from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...db.session import get_db


from ...models.user import User
from ...config.settings import settings
from ..deps import get_current_user
from ...schemas.auth import (
    UserCreate,
    UserResponse,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
)

router = APIRouter()

# ----- Security setup -----
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")



# ----- In‑memory user store (placeholder) -----
_users_db: Dict[str, Dict[str, Any]] = {}

class UserService:
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        return _users_db.get(email)

    async def create_user(self, email: str, hashed_password: str, full_name: Optional[str] = None) -> Dict[str, Any]:
        user = {
            "id": str(uuid.uuid4()),
            "email": email,
            "hashed_password": hashed_password,
            "full_name": full_name,
        }
        _users_db[email] = user
        return user

# ----- Helper functions -----
def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM,)

def create_refresh_token(data: dict):
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    payload = data.copy()
    payload.update({"exp": expire})

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

# ----- Endpoints -----
@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.email == user.email)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )

    db_user = User(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        hashed_password=get_password_hash(user.password),
        is_active=True,
        is_verified=False,
        role="USER",
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user

@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.email == login_data.email)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
        )

    if not verify_password(
        login_data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
        )

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

from jose import JWTError

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_data: RefreshRequest):
    try:
        payload = jwt.decode(
            refresh_data.refresh_token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token"
            )

        access_token = create_access_token({"sub": user_id})
        refresh_token = create_refresh_token({"sub": user_id})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token"
        )

@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user