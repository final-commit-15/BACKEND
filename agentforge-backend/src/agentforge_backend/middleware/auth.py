"""
Authentication Middleware

Supports both Supabase JWTs and legacy JWTs for backward compatibility.
"""
import logging
from typing import Optional
from fastapi import Request, Depends
from sqlalchemy import select
from uuid import UUID

from ..config.settings import settings
from ..security.jwt import decode_token, is_token_blacklisted, is_user_revoked
from ..db.session import async_session
from ..models.user import User
from ..utils.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


class SupabaseJWTVerifier:
    """Verify Supabase JWT tokens using the Supabase public key."""
    
    def __init__(self):
        self._public_key: Optional[str] = None
        self._key_fetched = False
    
    async def _fetch_public_key(self) -> str:
        """Fetch Supabase JWT public key from JWKS endpoint."""
        if self._key_fetched and self._public_key:
            return self._public_key
        
        if not settings.SUPABASE_URL:
            raise RuntimeError("SUPABASE_URL not configured")
        
        import httpx
        jwks_url = f"{settings.SUPABASE_URL}/auth/v1/jwks"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(jwks_url)
            response.raise_for_status()
            jwks = response.json()
            
            # Get the first key (Supabase typically has one)
            keys = jwks.get("keys", [])
            if not keys:
                raise RuntimeError("No keys found in Supabase JWKS")
            
            # Use the first RSA key
            key = keys[0]
            from jose import jwt
            self._public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
            self._key_fetched = True
            
            logger.info("Supabase JWT public key fetched successfully")
            return self._public_key
    
    async def verify(self, token: str) -> dict:
        """
        Verify a Supabase JWT token.
        
        Args:
            token: The JWT token
            
        Returns:
            Decoded token payload
            
        Raises:
            AuthenticationError: If token is invalid
        """
        from jose import jwt, JWTError
        
        try:
            public_key = await self._fetch_public_key()
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience="authenticated",
                issuer=f"{settings.SUPABASE_URL}/auth/v1",
            )
            return payload
        except JWTError as e:
            logger.warning(f"Supabase JWT verification failed: {e}")
            raise AuthenticationError("Invalid Supabase token") from e


# Global verifier instance
_supabase_verifier: Optional[SupabaseJWTVerifier] = None


async def get_supabase_verifier() -> SupabaseJWTVerifier:
    """Get or create the Supabase JWT verifier."""
    global _supabase_verifier
    if _supabase_verifier is None:
        _supabase_verifier = SupabaseJWTVerifier()
    return _supabase_verifier


def is_supabase_token(token: str) -> bool:
    """
    Check if a token is a Supabase token (RS256) vs legacy token (HS256).
    
    Supabase tokens use RS256 and have specific claims.
    Legacy tokens use HS256.
    """
    try:
        from jose import jwt
        # Decode header without verification
        header = jwt.get_unverified_header(token)
        alg = header.get("alg", "")
        # Supabase uses RS256, we use HS256
        return alg == "RS256"
    except Exception:
        return False


async def get_current_user_id(request: Request) -> str:
    """
    Get current user ID from request.
    
    Supports both Supabase JWTs (RS256) and legacy JWTs (HS256).
    
    Args:
        request: FastAPI request
        
    Returns:
        User ID string
        
    Raises:
        AuthenticationError: If authentication fails
    """
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise AuthenticationError("Missing or invalid token")
    
    token = auth.split(" ")[1]
    
    # Check if it's a Supabase token (RS256) or legacy token (HS256)
    if is_supabase_token(token):
        return await _verify_supabase_token(token, request)
    else:
        return await _verify_legacy_token(token, request)


async def _verify_supabase_token(token: str, request: Request) -> str:
    """Verify Supabase JWT token and extract user ID."""
    verifier = await get_supabase_verifier()
    payload = await verifier.verify(token)
    
    # Supabase tokens have 'sub' as user ID
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload")
    
    # Check token type
    if payload.get("type") != "access":
        raise AuthenticationError("Invalid token type")
    
    # Verify user exists in local database and is active
    async with async_session() as db:
        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")
    
    # Store user info in request state for downstream use
    request.state.supabase_user = payload
    request.state.user_id = user_id
    
    return user_id


async def _verify_legacy_token(token: str, request: Request) -> str:
    """Verify legacy HS256 JWT token."""
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


async def get_current_user(request: Request) -> User:
    """
    Get current user object from request.
    
    Args:
        request: FastAPI request
        
    Returns:
        User object
    """
    user_id = await get_current_user_id(request)
    
    async with async_session() as db:
        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()
        if not user:
            raise AuthenticationError("User not found")
        return user


async def get_optional_user_id(request: Request) -> Optional[str]:
    """
    Get current user ID if authenticated, None otherwise.
    
    Useful for endpoints that work for both authenticated and anonymous users.
    """
    try:
        return await get_current_user_id(request)
    except AuthenticationError:
        return None


async def get_supabase_user(request: Request) -> Optional[dict]:
    """
    Get Supabase user info from request state.
    
    Returns:
        Supabase user payload or None
    """
    return getattr(request.state, "supabase_user", None)