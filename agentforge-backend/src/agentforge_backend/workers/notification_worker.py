from .celery_app import celery_app
from ..services.notification_service import NotificationService
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.session import AsyncSessionLocal
import asyncio

@celery_app.task(name="send_notification")
def send_notification_task(user_id: str, type: str, title: str, message: str):
    async def _send():
        async with AsyncSessionLocal() as db:
            await NotificationService.create(db, user_id, type, title, message)
    asyncio.run(_send())