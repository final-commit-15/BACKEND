from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, OperationalError, DisconnectionError

from ..config.settings import settings
from ..db.session import async_session
from ..db.redis import get_redis_client
from ..models.user import User
from ..security.jwt import decode_token, is_token_blacklisted, is_user_revoked
from uuid import UUID
from ..utils.exceptions import AuthenticationError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# DB session dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    try:
        async with async_session() as session:
            yield session
    except (OperationalError, DisconnectionError) as e:
        raise HTTPException(status_code=503, detail="Database temporarily unavailable") from e
    except SQLAlchemyError as e:
        raise HTTPException(status_code=503, detail="Database error") from e

# Redis dependency
async def get_redis():
    return await get_redis_client()

# User authentication
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
        if not payload:
            raise credentials_exception
        
        # Check if token is blacklisted
        if await is_token_blacklisted(token, "access"):
            raise AuthenticationError("Token has been revoked")
        
        # Check token type
        if payload.get("type") != "access":
            raise credentials_exception
        
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        # Check if user tokens were revoked
        if await is_user_revoked(user_id):
            raise AuthenticationError("User tokens have been revoked")

        user_id = UUID(user_id)

    except (JWTError, ValueError, AuthenticationError):
        raise credentials_exception

    result = await db.execute(
        select(User).where(User.id == user_id)
    )

    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise AuthenticationError("Account disabled")

    return user

# Optional user dependency (for endpoints that work with or without auth)
async def get_current_user_optional(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None

# Permission check
async def require_permission(user: User, permission: str) -> bool:
    """Check if user has a specific permission."""
    from ..security.permissions import user_has_permission
    from ..models.user import UserRole
    return user_has_permission(user.role, permission)