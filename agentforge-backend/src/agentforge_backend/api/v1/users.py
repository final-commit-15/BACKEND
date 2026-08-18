from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ...db.session import get_db
from ...services.user_service import UserService
from ...middleware.auth import get_current_user_id
from ...schemas.user import UserOut, UserUpdate
from ...utils.exceptions import NotFoundError

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserOut)
async def get_me(current_user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    user = await UserService.get_by_id(db, current_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/me", response_model=UserOut)
async def update_me(data: UserUpdate, current_user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    return await UserService.update(db, current_user_id, data)

@router.get("/", response_model=List[UserOut])
async def list_users(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await UserService.list_users(db, skip, limit)