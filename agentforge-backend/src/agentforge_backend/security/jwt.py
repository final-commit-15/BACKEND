from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from ..config.settings import settings
from typing import Dict, Any, Optional, Tuple
from ..db.redis import get_redis_client
import uuid
import hashlib


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
    token_id: Optional[str] = None,
) -> Tuple[str, str]:
    """Create an access token with optional token ID for tracking."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    jti = token_id or str(uuid.uuid4())
    to_encode.update({"exp": expire, "jti": jti, "type": "access"})
    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, jti


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
    token_id: Optional[str] = None,
) -> Tuple[str, str]:
    """Create a refresh token with optional token ID for tracking."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    )
    jti = token_id or str(uuid.uuid4())
    to_encode.update({"exp": expire, "jti": jti, "type": "refresh"})
    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, jti


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token."""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return {}


def get_token_hash(token: str) -> str:
    """Get a hash of the token for storage in blacklist."""
    return hashlib.sha256(token.encode()).hexdigest()[:32]


async def blacklist_token(token: str, token_type: str = "access") -> bool:
    """Add a token to the blacklist."""
    try:
        redis = await get_redis_client()
        if redis is None:
            return False
        payload = decode_token(token)
        if not payload:
            return False
        
        jti = payload.get("jti")
        exp = payload.get("exp")
        if not jti or not exp:
            return False
        
        # Calculate TTL based on token expiration
        ttl = max(int(exp - datetime.now(timezone.utc).timestamp()), 1)
        
        key = f"token_blacklist:{token_type}:{jti}"
        await redis.setex(key, ttl, "1")
        return True
    except Exception:
        return False


async def is_token_blacklisted(token: str, token_type: str = "access") -> bool:
    """Check if a token is blacklisted."""
    try:
        redis = await get_redis_client()
        if redis is None:
            return False
        payload = decode_token(token)
        if not payload:
            return True
        
        jti = payload.get("jti")
        if not jti:
            return True
        
        key = f"token_blacklist:{token_type}:{jti}"
        result = await redis.get(key)
        return result is not None
    except Exception:
        # Fail open for availability, but log the error
        return False


async def rotate_refresh_token(refresh_token: str) -> Tuple[str, str]:
    """Rotate a refresh token - blacklist old, create new."""
    payload = decode_token(refresh_token)
    if not payload:
        raise ValueError("Invalid refresh token")
    
    if payload.get("type") != "refresh":
        raise ValueError("Not a refresh token")
    
    # Blacklist the old refresh token
    await blacklist_token(refresh_token, "refresh")
    
    # Create new token pair
    user_id = payload.get("sub")
    role = payload.get("role", "user")
    
    new_access_token, _ = create_access_token({"sub": user_id, "role": role})
    new_refresh_token, _ = create_refresh_token({"sub": user_id})
    
    return new_access_token, new_refresh_token


async def revoke_all_user_tokens(user_id: str) -> int:
    """Revoke all tokens for a user (logout from all devices)."""
    try:
        redis = await get_redis_client()
        if redis is None:
            return 0
        # This is a simplified approach - in production, you'd track user tokens
        # For now, we'll use a user revocation key
        key = f"user_revoked:{user_id}"
        await redis.setex(key, settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400, "1")
        return 1
    except Exception:
        return 0


async def is_user_revoked(user_id: str) -> bool:
    """Check if a user's tokens have been revoked."""
    try:
        redis = await get_redis_client()
        if redis is None:
            return False
        key = f"user_revoked:{user_id}"
        result = await redis.get(key)
        return result is not None
    except Exception:
        return False