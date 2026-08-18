from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ...db.session import get_db
from ...services.auth_service import AuthService
from ...schemas.auth import UserCreate, TokenResponse, LoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await AuthService.register(db, user_data)
    return await AuthService.login(db, user_data.email, user_data.password)

@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService.login(db, login_data.email, login_data.password)

@router.post("/refresh", response_model=TokenResponse)
async def refresh(refresh_token: str, db: AsyncSession = Depends(get_db)):
    return await AuthService.refresh_token(db, refresh_token)