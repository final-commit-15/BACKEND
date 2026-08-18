from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.webhook import Webhook
from ..schemas.webhook import WebhookCreate
from ..utils.exceptions import NotFoundError, PermissionDeniedError

class WebhookService:
    @staticmethod
    async def create(db: AsyncSession, data: WebhookCreate, user_id: str) -> Webhook:
        webhook = Webhook(**data.dict(), user_id=user_id)
        db.add(webhook)
        await db.commit()
        await db.refresh(webhook)
        return webhook

    @staticmethod
    async def list_by_user(db: AsyncSession, user_id: str):
        result = await db.execute(select(Webhook).where(Webhook.user_id == user_id))
        return result.scalars().all()

    @staticmethod
    async def delete(db: AsyncSession, webhook_id: str, user_id: str):
        webhook = await db.get(Webhook, webhook_id)
        if not webhook:
            raise NotFoundError("Webhook not found")
        if str(webhook.user_id) != user_id:
            raise PermissionDeniedError("Not your webhook")
        await db.delete(webhook)
        await db.commit()