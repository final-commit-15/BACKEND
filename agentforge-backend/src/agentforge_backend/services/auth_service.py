"""
Authentication Service

Handles authentication through Supabase Auth with backward compatibility
for legacy JWT tokens.
"""
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from ..models.user import User, UserRole
from ..security.password import hash_password, verify_password
from ..security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    blacklist_token,
    rotate_refresh_token,
    revoke_all_user_tokens,
    is_user_revoked,
    is_token_blacklisted,
)
from ..services.supabase_auth import get_supabase_auth_service
from ..schemas.auth import UserCreate, TokenResponse
from ..utils.exceptions import AuthenticationError, ConflictError, DatabaseError
from ..utils.logging import audit_logger


class AuthService:
    """Authentication service using Supabase Auth with legacy fallback."""
    
    @staticmethod
    async def register(db: AsyncSession, user_data: UserCreate) -> User:
        """
        Register a new user.
        
        Uses Supabase Auth for authentication and creates local user record.
        """
        try:
            # Check email in local DB
            existing_email = await db.execute(select(User).where(User.email == user_data.email))
            if existing_email.scalar_one_or_none():
                raise ConflictError("Email already registered")
            
            # Check username in local DB
            existing_username = await db.execute(select(User).where(User.username == user_data.username))
            if existing_username.scalar_one_or_none():
                raise ConflictError("Username already taken")
            
            # Register with Supabase Auth
            supabase_auth = await get_supabase_auth_service(use_admin=True)
            
            supabase_result = await supabase_auth.signup_email_password(
                email=user_data.email,
                password=user_data.password,
                full_name=user_data.full_name,
                username=user_data.username,
            )
            
            supabase_user = supabase_result["user"]
            supabase_session = supabase_result.get("session")
            
            # Create local user record linked to Supabase user
            hashed = hash_password(user_data.password)
            user = User(
                id=UUID(supabase_user["id"]),  # Use Supabase user ID
                email=user_data.email,
                username=user_data.username,
                hashed_password=hashed,  # Keep for legacy compatibility
                full_name=user_data.full_name,
                role=UserRole.USER,
                is_verified=supabase_user.get("email_confirmed_at") is not None,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            # Audit log
            audit_logger.log_auth(
                "register", 
                str(user.id), 
                "unknown", 
                True, 
                {"email": user.email, "provider": "supabase"}
            )
            
            return user
            
        except (ConflictError, AuthenticationError):
            raise
        except Exception as e:
            logging.getLogger(__name__).error(f"Register error: {type(e).__name__}: {e}")
            raise DatabaseError("Registration failed") from e
    
    @staticmethod
    async def login(db: AsyncSession, email: str, password: str, ip_address: str = None) -> TokenResponse:
        """
        Login user with email and password.
        
        Uses Supabase Auth for authentication.
        """
        try:
            supabase_auth = await get_supabase_auth_service(use_admin=False)
            
            result = await supabase_auth.login_email_password(
                email=email,
                password=password,
                ip_address=ip_address,
            )
            
            user = result["user"]
            session = result["session"]
            
            if not session:
                raise AuthenticationError("Failed to create session")
            
            # Get or create local user record
            supabase_user_id = UUID(user["id"])
            result = await db.execute(select(User).where(User.id == supabase_user_id))
            local_user = result.scalar_one_or_none()
            
            if not local_user:
                # Create local user record if doesn't exist
                local_user = User(
                    id=supabase_user_id,
                    email=user["email"],
                    username=user.get("user_metadata", {}).get("username", user["email"].split("@")[0]),
                    hashed_password="",  # Password managed by Supabase
                    full_name=user.get("user_metadata", {}).get("full_name", user["email"]),
                    role=UserRole.USER,
                    is_verified=user.get("email_confirmed_at") is not None,
                )
                db.add(local_user)
                await db.commit()
                await db.refresh(local_user)
            elif not local_user.is_active:
                raise AuthenticationError("Account disabled")
            
            # Use Supabase session tokens
            access_token = session["access_token"]
            refresh_token = session["refresh_token"]
            
            audit_logger.log_auth(
                "login", 
                str(local_user.id), 
                ip_address or "unknown", 
                True, 
                {"email": email, "provider": "supabase"}
            )
            
            return TokenResponse(
                access_token=access_token, 
                refresh_token=refresh_token, 
                token_type="bearer"
            )
            
        except AuthenticationError:
            raise
        except Exception as e:
            logging.getLogger(__name__).error(f"Login error: {type(e).__name__}: {e}")
            raise DatabaseError("Login failed") from e
    
    @staticmethod
    async def refresh_token(db: AsyncSession, refresh_token: str, ip_address: str = None, rotate: bool = None) -> TokenResponse:
        """
        Refresh access token using Supabase Auth.
        """
        try:
            if rotate is None:
                from ..config.settings import settings
                rotate = settings.JWT_REFRESH_TOKEN_ROTATION
            
            supabase_auth = await get_supabase_auth_service(use_admin=False)
            
            result = await supabase_auth.refresh_session(
                refresh_token=refresh_token,
                ip_address=ip_address,
            )
            
            session = result.get("session")
            user = result.get("user")
            
            if not session:
                raise AuthenticationError("Failed to refresh session")
            
            audit_logger.log_auth(
                "refresh", 
                str(user["id"]) if user else "unknown", 
                ip_address or "unknown", 
                True, 
                {}
            )
            
            return TokenResponse(
                access_token=session["access_token"],
                refresh_token=session["refresh_token"],
                token_type="bearer",
            )
            
        except AuthenticationError:
            raise
        except Exception as e:
            logging.getLogger(__name__).error(f"Refresh token error: {type(e).__name__}: {e}")
            raise DatabaseError("Token refresh failed") from e
    
    @staticmethod
    async def logout(db: AsyncSession, user_id: str, access_token: str = None, refresh_token: str = None, revoke_all: bool = False, ip_address: str = None) -> bool:
        """
        Logout user - delegate to Supabase Auth.
        """
        try:
            if revoke_all:
                supabase_auth = await get_supabase_auth_service(use_admin=True)
                await supabase_auth.admin_update_user(user_id, {"password": None})  # Force re-auth
                audit_logger.log_auth("logout", user_id, ip_address or "unknown", True, {"revoke_all": True})
            else:
                supabase_auth = await get_supabase_auth_service(use_admin=False)
                if access_token:
                    await supabase_auth.logout(access_token, ip_address)
                audit_logger.log_auth("logout", user_id, ip_address or "unknown", True, {"revoke_all": False})
            return True
        except Exception as e:
            logging.getLogger(__name__).error(f"Logout error: {type(e).__name__}: {e}")
            raise DatabaseError("Logout failed") from e
    
    @staticmethod
    async def request_password_reset(email: str, redirect_to: str = None) -> bool:
        """Request password reset through Supabase."""
        try:
            supabase_auth = await get_supabase_auth_service(use_admin=False)
            return await supabase_auth.request_password_reset(email, redirect_to)
        except Exception as e:
            logging.getLogger(__name__).error(f"Password reset request error: {e}")
            return False
    
    @staticmethod
    async def update_password(access_token: str, new_password: str) -> bool:
        """Update user password through Supabase."""
        try:
            supabase_auth = await get_supabase_auth_service(use_admin=False)
            return await supabase_auth.update_password(access_token, new_password)
        except Exception as e:
            logging.getLogger(__name__).error(f"Update password error: {e}")
            raise AuthenticationError("Failed to update password") from e
    
    @staticmethod
    async def send_magic_link(email: str, redirect_to: str = None) -> bool:
        """Send magic link for passwordless login."""
        try:
            supabase_auth = await get_supabase_auth_service(use_admin=False)
            result = await supabase_auth.send_magic_link(email, redirect_to)
            return result.get("success", False)
        except Exception as e:
            logging.getLogger(__name__).error(f"Magic link error: {e}")
            return False
    
    @staticmethod
    async def verify_magic_link(token: str) -> TokenResponse:
        """Verify magic link and return tokens."""
        try:
            supabase_auth = await get_supabase_auth_service(use_admin=False)
            result = await supabase_auth.verify_magic_link(token)
            
            session = result.get("session")
            if not session:
                raise AuthenticationError("Invalid magic link")
            
            return TokenResponse(
                access_token=session["access_token"],
                refresh_token=session["refresh_token"],
                token_type="bearer",
            )
        except AuthenticationError:
            raise
        except Exception as e:
            logging.getLogger(__name__).error(f"Magic link verify error: {e}")
            raise AuthenticationError("Invalid magic link") from e
    
    @staticmethod
    async def get_oauth_url(provider: str, redirect_to: str = None, scopes: str = None) -> str:
        """Get OAuth authorization URL."""
        try:
            supabase_auth = await get_supabase_auth_service(use_admin=False)
            result = await supabase_auth.get_oauth_url(provider, redirect_to, scopes)
            return result["url"]
        except Exception as e:
            logging.getLogger(__name__).error(f"OAuth URL error: {e}")
            raise AuthenticationError(f"Failed to get {provider} OAuth URL") from e
    
    @staticmethod
    async def handle_oauth_callback(code: str, redirect_to: str = None) -> TokenResponse:
        """Handle OAuth callback."""
        try:
            supabase_auth = await get_supabase_auth_service(use_admin=False)
            result = await supabase_auth.handle_oauth_callback(code, redirect_to)
            
            session = result.get("session")
            if not session:
                raise AuthenticationError("OAuth authentication failed")
            
            return TokenResponse(
                access_token=session["access_token"],
                refresh_token=session["refresh_token"],
                token_type="bearer",
            )
        except AuthenticationError:
            raise
        except Exception as e:
            logging.getLogger(__name__).error(f"OAuth callback error: {e}")
            raise AuthenticationError("OAuth authentication failed") from e