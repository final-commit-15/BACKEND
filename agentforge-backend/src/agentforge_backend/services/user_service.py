from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.user import User
from ..security.password import hash_password
from ..schemas.user import UserUpdate
from ..utils.exceptions import NotFoundError

class UserService:
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: str) -> User | None:
        return await db.get(User, user_id)

    @staticmethod
    async def update(db: AsyncSession, user_id: str, data: UserUpdate) -> User:
        user = await db.get(User, user_id)
        if not user:
            raise NotFoundError("User not found")
        if data.username:
            user.username = data.username
        if data.full_name:
            user.full_name = data.full_name
        if data.password:
            user.hashed_password = hash_password(data.password)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def list_users(db: AsyncSession, skip: int = 0, limit: int = 100):
        result = await db.execute(select(User).offset(skip).limit(limit))
        return result.scalars().all()