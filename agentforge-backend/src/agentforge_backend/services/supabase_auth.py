"""
Supabase Authentication Service

Handles all authentication operations through Supabase Auth including:
- Email/password signup and login
- Magic link authentication
- OAuth providers (Google, GitHub)
- Token refresh and session management
- User management (admin operations)
"""
import logging
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timedelta

from supabase import Client
from gotrue import User as GotrueUser, Session
from gotrue.errors import AuthApiError, AuthRetryableError

from ..core.supabase import get_supabase_admin, get_supabase
from ..config.settings import settings
from ..utils.exceptions import AuthenticationError, ConflictError, DatabaseError
from ..utils.logging import audit_logger

logger = logging.getLogger(__name__)


class SupabaseAuthService:
    """Service for managing authentication through Supabase Auth."""
    
    def __init__(self, use_admin: bool = True):
        """
        Initialize the auth service.
        
        Args:
            use_admin: If True, use service role client for admin operations.
                      If False, use anon client for user-facing operations.
        """
        self._use_admin = use_admin
        self._client: Optional[Client] = None
    
    @property
    async def client(self) -> Client:
        """Get the Supabase client."""
        if self._client is None:
            if self._use_admin:
                self._client = await get_supabase_admin()
            else:
                self._client = await get_supabase()
        return self._client
    
    def _get_client_sync(self) -> Client:
        """Get synchronous client for non-async operations."""
        if self._use_admin:
            return get_supabase_admin_sync()
        return get_supabase_sync()
    
    # ==================== User Registration ====================
    
    async def signup_email_password(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        username: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Register a new user with email and password.
        
        Args:
            email: User's email address
            password: User's password
            full_name: User's full name
            username: Desired username
            metadata: Additional user metadata
            
        Returns:
            Dict with user and session data
            
        Raises:
            ConflictError: If email already exists
            AuthenticationError: If registration fails
        """
        try:
            client = await self.client
            
            user_metadata = metadata or {}
            if full_name:
                user_metadata["full_name"] = full_name
            if username:
                user_metadata["username"] = username
            
            # Supabase signup
            response = await client.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True,  # Auto-confirm for development
                "user_metadata": user_metadata,
            })
            
            user = response.user
            if not user:
                raise AuthenticationError("Failed to create user")
            
            # Create session for the user
            session_response = await client.auth.sign_in_with_password({
                "email": email,
                "password": password,
            })
            
            audit_logger.log_auth(
                "signup", 
                str(user.id), 
                "unknown", 
                True, 
                {"email": email, "provider": "email"}
            )
            
            return {
                "user": self._format_user(user),
                "session": self._format_session(session_response.session) if session_response.session else None,
            }
            
        except AuthApiError as e:
            if "already registered" in str(e).lower() or "already exists" in str(e).lower():
                raise ConflictError("Email already registered")
            logger.error(f"Supabase signup error: {e}")
            raise AuthenticationError(f"Registration failed: {str(e)}")
        except Exception as e:
            logger.error(f"Signup error: {type(e).__name__}: {e}")
            raise AuthenticationError("Registration failed") from e
    
    # ==================== User Login ====================
    
    async def login_email_password(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Authenticate user with email and password.
        
        Args:
            email: User's email
            password: User's password
            ip_address: Client IP address for audit logging
            
        Returns:
            Dict with user and session data
            
        Raises:
            AuthenticationError: If credentials are invalid
        """
        try:
            client = await self.client
            
            response = await client.auth.sign_in_with_password({
                "email": email,
                "password": password,
            })
            
            user = response.user
            session = response.session
            
            if not user or not session:
                raise AuthenticationError("Invalid credentials")
            
            audit_logger.log_auth(
                "login",
                str(user.id),
                ip_address or "unknown",
                True,
                {"email": email, "provider": "email"}
            )
            
            return {
                "user": self._format_user(user),
                "session": self._format_session(session),
            }
            
        except AuthApiError as e:
            if "invalid credentials" in str(e).lower() or "invalid login" in str(e).lower():
                audit_logger.log_auth(
                    "login",
                    "unknown",
                    ip_address or "unknown",
                    False,
                    {"email": email, "reason": "invalid_credentials"}
                )
                raise AuthenticationError("Invalid credentials")
            logger.error(f"Supabase login error: {e}")
            raise AuthenticationError("Login failed") from e
        except Exception as e:
            logger.error(f"Login error: {type(e).__name__}: {e}")
            raise AuthenticationError("Login failed") from e
    
    # ==================== Magic Link ====================
    
    async def send_magic_link(
        self,
        email: str,
        redirect_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a magic link for passwordless login.
        
        Args:
            email: User's email address
            redirect_to: URL to redirect after login
            
        Returns:
            Dict with success status
        """
        try:
            client = await self.client
            
            options = {}
            if redirect_to:
                options["redirect_to"] = redirect_to
            
            await client.auth.sign_in_with_otp({
                "email": email,
                "options": options,
            })
            
            audit_logger.log_auth(
                "magic_link_sent",
                "unknown",
                "unknown",
                True,
                {"email": email}
            )
            
            return {"success": True, "message": "Magic link sent"}
            
        except AuthApiError as e:
            logger.error(f"Magic link error: {e}")
            raise AuthenticationError("Failed to send magic link") from e
    
    async def verify_magic_link(
        self,
        token: str,
        type: str = "magiclink",
    ) -> Dict[str, Any]:
        """
        Verify a magic link token and create session.
        
        Args:
            token: The magic link token
            type: Token type (magiclink, email, phone)
            
        Returns:
            Dict with user and session data
        """
        try:
            client = await self.client
            
            response = await client.auth.verify_otp({
                "token": token,
                "type": type,
            })
            
            user = response.user
            session = response.session
            
            if not user or not session:
                raise AuthenticationError("Invalid or expired magic link")
            
            audit_logger.log_auth(
                "magic_link_verify",
                str(user.id),
                "unknown",
                True,
                {"provider": "magic_link"}
            )
            
            return {
                "user": self._format_user(user),
                "session": self._format_session(session),
            }
            
        except AuthApiError as e:
            logger.error(f"Magic link verify error: {e}")
            raise AuthenticationError("Invalid or expired magic link") from e
    
    # ==================== OAuth ====================
    
    async def get_oauth_url(
        self,
        provider: str,
        redirect_to: Optional[str] = None,
        scopes: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Get OAuth authorization URL for a provider.
        
        Args:
            provider: OAuth provider (google, github, etc.)
            redirect_to: Custom redirect URL
            scopes: Additional OAuth scopes
            
        Returns:
            Dict with authorization URL
        """
        try:
            client = await self.client
            
            options = {}
            if redirect_to:
                options["redirect_to"] = redirect_to
            if scopes:
                options["scopes"] = scopes
            
            response = await client.auth.sign_in_with_oauth({
                "provider": provider,
                "options": options,
            })
            
            return {"url": response.url}
            
        except AuthApiError as e:
            logger.error(f"OAuth URL error for {provider}: {e}")
            raise AuthenticationError(f"Failed to get {provider} OAuth URL") from e
    
    async def handle_oauth_callback(
        self,
        code: str,
        redirect_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Handle OAuth callback and exchange code for session.
        
        Args:
            code: Authorization code from OAuth provider
            redirect_to: Redirect URL used in authorization
            
        Returns:
            Dict with user and session data
        """
        try:
            client = await self.client
            
            response = await client.auth.exchange_code_for_session({
                "auth_code": code,
            })
            
            user = response.user
            session = response.session
            
            if not user or not session:
                raise AuthenticationError("OAuth authentication failed")
            
            audit_logger.log_auth(
                "oauth_callback",
                str(user.id),
                "unknown",
                True,
                {"provider": "oauth"}
            )
            
            return {
                "user": self._format_user(user),
                "session": self._format_session(session),
            }
            
        except AuthApiError as e:
            logger.error(f"OAuth callback error: {e}")
            raise AuthenticationError("OAuth authentication failed") from e
    
    # ==================== Session Management ====================
    
    async def refresh_session(
        self,
        refresh_token: str,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: The refresh token
            ip_address: Client IP for audit logging
            
        Returns:
            Dict with new session data
        """
        try:
            client = await self.client
            
            response = await client.auth.refresh_session(refresh_token)
            
            session = response.session
            user = response.user
            
            if not session:
                raise AuthenticationError("Failed to refresh session")
            
            audit_logger.log_auth(
                "refresh",
                str(user.id) if user else "unknown",
                ip_address or "unknown",
                True,
                {}
            )
            
            return {
                "user": self._format_user(user) if user else None,
                "session": self._format_session(session),
            }
            
        except AuthApiError as e:
            logger.error(f"Session refresh error: {e}")
            raise AuthenticationError("Failed to refresh session") from e
    
    async def logout(
        self,
        access_token: str,
        ip_address: Optional[str] = None,
    ) -> bool:
        """
        Logout user by signing out session.
        
        Args:
            access_token: User's access token
            ip_address: Client IP for audit logging
            
        Returns:
            True if successful
        """
        try:
            client = await self.client
            
            # Set the auth header for the client
            client.auth.set_session(access_token, "")
            
            await client.auth.sign_out()
            
            # Decode token to get user ID for audit
            try:
                from ..security.jwt import decode_token
                payload = decode_token(access_token)
                user_id = payload.get("sub") if payload else "unknown"
            except Exception:
                user_id = "unknown"
            
            audit_logger.log_auth(
                "logout",
                user_id,
                ip_address or "unknown",
                True,
                {}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False
    
    async def get_user(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user from access token.
        
        Args:
            access_token: User's access token
            
        Returns:
            User dict or None if invalid
        """
        try:
            client = await self.client
            client.auth.set_session(access_token, "")
            
            user = await client.auth.get_user()
            
            if user and user.user:
                return self._format_user(user.user)
            return None
            
        except Exception as e:
            logger.error(f"Get user error: {e}")
            return None
    
    # ==================== Admin Operations ====================
    
    async def admin_create_user(
        self,
        email: str,
        password: Optional[str] = None,
        email_confirm: bool = True,
        user_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a user as admin (bypasses email confirmation).
        
        Args:
            email: User's email
            password: User's password (optional)
            email_confirm: Whether to confirm email immediately
            user_metadata: Additional metadata
            
        Returns:
            Created user data
        """
        try:
            client = await get_supabase_admin()
            
            user_data = {
                "email": email,
                "email_confirm": email_confirm,
            }
            if password:
                user_data["password"] = password
            if user_metadata:
                user_data["user_metadata"] = user_metadata
            
            response = await client.auth.admin.create_user(user_data)
            
            if not response.user:
                raise AuthenticationError("Failed to create user")
            
            return self._format_user(response.user)
            
        except AuthApiError as e:
            if "already registered" in str(e).lower():
                raise ConflictError("Email already registered")
            logger.error(f"Admin create user error: {e}")
            raise AuthenticationError("Failed to create user") from e
    
    async def admin_delete_user(self, user_id: str) -> bool:
        """
        Delete a user as admin.
        
        Args:
            user_id: User ID to delete
            
        Returns:
            True if successful
        """
        try:
            client = await get_supabase_admin()
            
            await client.auth.admin.delete_user(user_id)
            
            audit_logger.log_auth(
                "admin_delete_user",
                user_id,
                "system",
                True,
                {}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Admin delete user error: {e}")
            return False
    
    async def admin_update_user(
        self,
        user_id: str,
        updates: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Update user as admin.
        
        Args:
            user_id: User ID to update
            updates: Fields to update (email, password, user_metadata, etc.)
            
        Returns:
            Updated user data
        """
        try:
            client = await get_supabase_admin()
            
            response = await client.auth.admin.update_user_by_id(
                user_id,
                updates,
            )
            
            if not response.user:
                raise AuthenticationError("Failed to update user")
            
            return self._format_user(response.user)
            
        except Exception as e:
            logger.error(f"Admin update user error: {e}")
            raise AuthenticationError("Failed to update user") from e
    
    async def admin_list_users(
        self,
        page: int = 1,
        per_page: int = 50,
    ) -> Dict[str, Any]:
        """
        List all users (admin only).
        
        Args:
            page: Page number
            per_page: Users per page
            
        Returns:
            Dict with users list and pagination
        """
        try:
            client = await get_supabase_admin()
            
            response = await client.auth.admin.list_users(
                page=page,
                per_page=per_page,
            )
            
            users = [self._format_user(u) for u in response.users]
            
            return {
                "users": users,
                "total": response.total,
                "page": page,
                "per_page": per_page,
            }
            
        except Exception as e:
            logger.error(f"Admin list users error: {e}")
            raise DatabaseError("Failed to list users") from e
    
    async def admin_send_password_reset(
        self,
        email: str,
        redirect_to: Optional[str] = None,
    ) -> bool:
        """
        Send password reset email as admin.
        
        Args:
            email: User's email
            redirect_to: Reset password redirect URL
            
        Returns:
            True if successful
        """
        try:
            client = await get_supabase_admin()
            
            options = {}
            if redirect_to:
                options["redirect_to"] = redirect_to
            
            await client.auth.admin.generate_link({
                "type": "recovery",
                "email": email,
                "options": options,
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Admin password reset error: {e}")
            return False
    
    # ==================== User Metadata ====================
    
    async def update_user_metadata(
        self,
        access_token: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Update current user's metadata.
        
        Args:
            access_token: User's access token
            metadata: Metadata to update
            
        Returns:
            Updated user data
        """
        try:
            client = await self.client
            client.auth.set_session(access_token, "")
            
            response = await client.auth.update_user({
                "data": metadata,
            })
            
            if not response.user:
                raise AuthenticationError("Failed to update metadata")
            
            return self._format_user(response.user)
            
        except Exception as e:
            logger.error(f"Update metadata error: {e}")
            raise AuthenticationError("Failed to update metadata") from e
    
    # ==================== Helpers ====================
    
    def _format_user(self, user: GotrueUser) -> Dict[str, Any]:
        """Format Gotrue user to dict."""
        return {
            "id": str(user.id),
            "email": user.email,
            "phone": user.phone,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "last_sign_in_at": user.last_sign_in_at,
            "email_confirmed_at": user.email_confirmed_at,
            "phone_confirmed_at": user.phone_confirmed_at,
            "is_anonymous": user.is_anonymous,
            "user_metadata": user.user_metadata or {},
            "app_metadata": user.app_metadata or {},
            "identities": [
                {
                    "id": str(ident.id),
                    "provider": ident.provider,
                    "identity_data": ident.identity_data,
                }
                for ident in (user.identities or [])
            ],
        }
    
    def _format_session(self, session: Session) -> Dict[str, Any]:
        """Format Gotrue session to dict."""
        return {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "expires_in": session.expires_in,
            "expires_at": session.expires_at,
            "token_type": session.token_type,
            "user": self._format_user(session.user) if session.user else None,
        }
    
    # ==================== Password Reset ====================
    
    async def request_password_reset(
        self,
        email: str,
        redirect_to: Optional[str] = None,
    ) -> bool:
        """
        Request password reset email.
        
        Args:
            email: User's email
            redirect_to: Custom redirect URL after reset
            
        Returns:
            True if successful
        """
        try:
            client = await self.client
            
            options = {}
            if redirect_to:
                options["redirect_to"] = redirect_to
            
            await client.auth.reset_password_for_email(email, options)
            return True
            
        except Exception as e:
            logger.error(f"Password reset request error: {e}")
            return False
    
    async def update_password(
        self,
        access_token: str,
        new_password: str,
    ) -> bool:
        """
        Update user's password.
        
        Args:
            access_token: User's access token
            new_password: New password
            
        Returns:
            True if successful
        """
        try:
            client = await self.client
            client.auth.set_session(access_token, "")
            
            await client.auth.update_user({"password": new_password})
            return True
            
        except Exception as e:
            logger.error(f"Update password error: {e}")
            raise AuthenticationError("Failed to update password") from e


# Global service instance
_supabase_auth_service: Optional[SupabaseAuthService] = None


async def get_supabase_auth_service(use_admin: bool = True) -> SupabaseAuthService:
    """Get or create the Supabase auth service."""
    global _supabase_auth_service
    
    if _supabase_auth_service is None:
        _supabase_auth_service = SupabaseAuthService(use_admin=use_admin)
    
    return _supabase_auth_service