from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ...db.session import get_db
from ...services.auth_service import AuthService
from ...schemas.auth import (
    UserCreate,
    UserResponse,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    LogoutRequest,
)
from ...utils.exceptions import AuthenticationError, ConflictError
from ...middleware.rate_limiter import limiter
from ...utils.logging import get_logger

router = APIRouter()
logger = get_logger("auth")


@router.post("/register", response_model=UserResponse, status_code=201)
@limiter.limit("3/minute")
async def register(
    request: Request,
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user."""
    try:
        db_user = await AuthService.register(db, user)
        return db_user
    except ConflictError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("registration_failed", error=str(e), email=user.email)
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login user and return access and refresh tokens."""
    try:
        ip = request.client.host if request.client else None
        tokens = await AuthService.login(db, login_data.email, login_data.password, ip)
        return tokens
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("login_failed", error=str(e), email=login_data.email)
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")
async def refresh_token(
    request: Request,
    refresh_data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token."""
    try:
        ip = request.client.host if request.client else None
        tokens = await AuthService.refresh_token(db, refresh_data.refresh_token, ip)
        return tokens
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("token_refresh_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Token refresh failed")


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    logout_data: LogoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """Logout user and optionally revoke all tokens."""
    try:
        ip = request.client.host if request.client else None
        await AuthService.logout(
            db,
            current_user_id,
            access_token=logout_data.access_token,
            refresh_token=logout_data.refresh_token,
            revoke_all=logout_data.revoke_all,
            ip_address=ip,
        )
    except Exception as e:
        logger.error("logout_failed", error=str(e), user_id=current_user_id)
        raise HTTPException(status_code=500, detail="Logout failed")


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return current_user


# Import at bottom to avoid circular imports
from ..deps import get_current_user
from ...models.user import User
from ...middleware.auth import get_current_user_id