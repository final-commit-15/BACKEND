from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.user import User, UserRole
from ..security.password import hash_password, verify_password
from ..security.jwt import create_access_token, create_refresh_token, decode_token
from ..schemas.auth import UserCreate, TokenResponse
from ..utils.exceptions import AuthenticationError, ConflictError

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
        return user

    @staticmethod
    async def login(db: AsyncSession, email: str, password: str) -> TokenResponse:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid credentials")
        if not user.is_active:
            raise AuthenticationError("Account disabled")
        access = create_access_token({"sub": str(user.id), "role": user.role.value})
        refresh = create_refresh_token({"sub": str(user.id)})
        return TokenResponse(access_token=access, refresh_token=refresh, token_type="bearer")

    @staticmethod
    async def refresh_token(db: AsyncSession, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)
        if not payload:
            raise AuthenticationError("Invalid token")
        user_id = payload.get("sub")
        user = await db.get(User, user_id)
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")
        access = create_access_token({"sub": str(user.id), "role": user.role.value})
        return TokenResponse(access_token=access, refresh_token=refresh_token, token_type="bearer")