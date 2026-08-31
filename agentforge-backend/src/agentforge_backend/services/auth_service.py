from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.user import User, UserRole
from ..security.password import hash_password, verify_password
from ..security.jwt import (
    create_access_token, 
    create_refresh_token, 
    decode_token,
    blacklist_token,
    rotate_refresh_token,
    revoke_all_user_tokens,
)
from ..schemas.auth import UserCreate, TokenResponse
from ..utils.exceptions import AuthenticationError, ConflictError
from ..utils.logging import audit_logger


class AuthService:
    @staticmethod
    async def register(db: AsyncSession, user_data: UserCreate) -> User:
        # Check email
        existing_email = await db.execute(select(User).where(User.email == user_data.email))
        if existing_email.scalar_one_or_none():
            raise ConflictError("Email already registered")

        # Check username (critical fix)
        existing_username = await db.execute(select(User).where(User.username == user_data.username))
        if existing_username.scalar_one_or_none():
            raise ConflictError("Username already taken")

        hashed = hash_password(user_data.password)
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed,
            full_name=user_data.full_name,
            role=UserRole.USER
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Audit log
        audit_logger.log_auth("register", str(user.id), "unknown", True, {"email": user.email})
        
        return user

    @staticmethod
    async def login(db: AsyncSession, email: str, password: str, ip_address: str = None) -> TokenResponse:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            audit_logger.log_auth("login", "unknown", ip_address or "unknown", False, {"email": email, "reason": "invalid_credentials"})
            raise AuthenticationError("Invalid credentials")
        if not user.is_active:
            audit_logger.log_auth("login", str(user.id), ip_address or "unknown", False, {"email": email, "reason": "account_disabled"})
            raise AuthenticationError("Account disabled")
        
        access, _ = create_access_token({"sub": str(user.id), "role": user.role.value})
        refresh, _ = create_refresh_token({"sub": str(user.id)})
        
        audit_logger.log_auth("login", str(user.id), ip_address or "unknown", True, {"email": user.email})
        
        return TokenResponse(access_token=access, refresh_token=refresh, token_type="bearer")

    @staticmethod
    async def refresh_token(db: AsyncSession, refresh_token: str, ip_address: str = None, rotate: bool = None) -> TokenResponse:
        if rotate is None:
            from ..config.settings import settings
            rotate = settings.JWT_REFRESH_TOKEN_ROTATION
        
        payload = decode_token(refresh_token)
        if not payload:
            audit_logger.log_auth("refresh", "unknown", ip_address or "unknown", False, {"reason": "invalid_token"})
            raise AuthenticationError("Invalid token")
        
        if payload.get("type") != "refresh":
            audit_logger.log_auth("refresh", "unknown", ip_address or "unknown", False, {"reason": "not_refresh_token"})
            raise AuthenticationError("Invalid token type")
        
        user_id = payload.get("sub")
        user = await db.get(User, user_id)
        if not user or not user.is_active:
            audit_logger.log_auth("refresh", user_id or "unknown", ip_address or "unknown", False, {"reason": "user_not_found_or_inactive"})
            raise AuthenticationError("User not found or inactive")
        
        # Check if user tokens were revoked
        from ..security.jwt import is_user_revoked
        if await is_user_revoked(str(user.id)):
            audit_logger.log_auth("refresh", str(user.id), ip_address or "unknown", False, {"reason": "tokens_revoked"})
            raise AuthenticationError("Tokens revoked")
        
        # Check if refresh token is blacklisted
        from ..security.jwt import is_token_blacklisted
        if await is_token_blacklisted(refresh_token, "refresh"):
            audit_logger.log_auth("refresh", str(user.id), ip_address or "unknown", False, {"reason": "token_blacklisted"})
            raise AuthenticationError("Token revoked")
        
        if rotate:
            # Rotate refresh token
            access, refresh = await rotate_refresh_token(refresh_token)
        else:
            access, _ = create_access_token({"sub": str(user.id), "role": user.role.value})
            refresh = refresh_token
        
        audit_logger.log_auth("refresh", str(user.id), ip_address or "unknown", True)
        
        return TokenResponse(access_token=access, refresh_token=refresh, token_type="bearer")

    @staticmethod
    async def logout(db: AsyncSession, user_id: str, access_token: str = None, refresh_token: str = None, revoke_all: bool = False, ip_address: str = None) -> bool:
        """Logout user - blacklist tokens."""
        try:
            if revoke_all:
                await revoke_all_user_tokens(user_id)
                audit_logger.log_auth("logout", user_id, ip_address or "unknown", True, {"revoke_all": True})
            else:
                if access_token:
                    await blacklist_token(access_token, "access")
                if refresh_token:
                    await blacklist_token(refresh_token, "refresh")
                audit_logger.log_auth("logout", user_id, ip_address or "unknown", True, {"revoke_all": False})
            return True
        except Exception:
            audit_logger.log_auth("logout", user_id, ip_address or "unknown", False)
            return False