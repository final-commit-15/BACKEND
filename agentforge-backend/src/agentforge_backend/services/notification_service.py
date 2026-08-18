from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.notification import Notification
from ..utils.exceptions import NotFoundError, PermissionDeniedError

class NotificationService:
    @staticmethod
    async def list_by_user(db: AsyncSession, user_id: str):
        result = await db.execute(select(Notification).where(Notification.user_id == user_id).order_by(Notification.created_at.desc()))
        return result.scalars().all()

    @staticmethod
    async def mark_read(db: AsyncSession, notification_id: str, user_id: str):
        notif = await db.get(Notification, notification_id)
        if not notif:
            raise NotFoundError("Notification not found")
        if str(notif.user_id) != user_id:
            raise PermissionDeniedError("Not your notification")
        notif.is_read = True
        await db.commit()
        await db.refresh(notif)
        return notif

    @staticmethod
    async def create(db: AsyncSession, user_id: str, type: str, title: str, message: str):
        notif = Notification(user_id=user_id, type=type, title=title, message=message)
        db.add(notif)
        await db.commit()
        await db.refresh(notif)
        return notif