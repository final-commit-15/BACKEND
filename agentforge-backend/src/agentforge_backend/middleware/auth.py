from fastapi import Request, HTTPException, status, Depends
from ..security.jwt import decode_token, is_token_blacklisted, is_user_revoked
from ..utils.exceptions import AuthenticationError
from ..db.session import async_session
from ..models.user import User
from sqlalchemy import select
from uuid import UUID


async def get_current_user_id(request: Request) -> str:
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise AuthenticationError("Missing or invalid token")
    token = auth.split(" ")[1]
    payload = decode_token(token)
    if not payload:
        raise AuthenticationError("Invalid token")
    
    # Check if token is blacklisted
    if await is_token_blacklisted(token, "access"):
        raise AuthenticationError("Token has been revoked")
    
    if payload.get("type") != "access":
        raise AuthenticationError("Invalid token type")
    
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload")
    
    # Check if user tokens were revoked
    if await is_user_revoked(user_id):
        raise AuthenticationError("User tokens have been revoked")
    
    # Verify user exists and is active
    async with async_session() as db:
        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")
    
    return user_id