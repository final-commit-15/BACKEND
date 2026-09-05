from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from typing import Dict, Any, Optional
from ..models.activity import ActivityLog
from ..models.user import User

class ActivityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_activity_log(self, workspace_id: UUID, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        offset = (page - 1) * limit
        count_stmt = select(func.count()).select_from(ActivityLog).where(ActivityLog.workspace_id == workspace_id)
        total = (await self.db.execute(count_stmt)).scalar()

        stmt = select(ActivityLog).where(ActivityLog.workspace_id == workspace_id)\
            .order_by(ActivityLog.created_at.desc())\
            .offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        items = result.scalars().all()
        items_data = []
        for log in items:
            user_stmt = select(User).where(User.id == log.user_id)
            user = (await self.db.execute(user_stmt)).scalar_one_or_none()
            items_data.append({
                "id": str(log.id),
                "type": log.type,
                "action": log.action,
                "user": user.full_name if user else str(log.user_id),
                "created_at": log.created_at.isoformat(),
                "extra_data": log.extra_data,   # changed
            })
        return {
            "page": page,
            "limit": limit,
            "total": total or 0,
            "items": items_data,
        }

    async def get_activity_by_id(self, activity_id: UUID, workspace_id: UUID) -> Optional[Dict[str, Any]]:
        stmt = select(ActivityLog).where(ActivityLog.id == activity_id, ActivityLog.workspace_id == workspace_id)
        log = (await self.db.execute(stmt)).scalar_one_or_none()
        if not log:
            return None
        user_stmt = select(User).where(User.id == log.user_id)
        user = (await self.db.execute(user_stmt)).scalar_one_or_none()
        return {
            "id": str(log.id),
            "type": log.type,
            "action": log.action,
            "user": user.full_name if user else str(log.user_id),
            "created_at": log.created_at.isoformat(),
            "extra_data": log.extra_data,
        }