from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.integration import Integration
from ..schemas.integration import IntegrationCreate
from ..utils.exceptions import NotFoundError, PermissionDeniedError
from cryptography.fernet import Fernet
from ..config.settings import settings
import json

# In production, use a fixed key from env; for demo, derive from JWT_SECRET
cipher = Fernet(Fernet.generate_key())  # TODO: store securely

class IntegrationService:
    @staticmethod
    async def connect(db: AsyncSession, data: IntegrationCreate, user_id: str) -> Integration:
        encrypted = cipher.encrypt(json.dumps(data.credentials).encode()).decode()
        integration = Integration(
            name=data.name,
            provider=data.provider,
            encrypted_credentials=encrypted,
            config=data.config,
            user_id=user_id
        )
        db.add(integration)
        await db.commit()
        await db.refresh(integration)
        return integration

    @staticmethod
    async def list_by_user(db: AsyncSession, user_id: str):
        result = await db.execute(select(Integration).where(Integration.user_id == user_id))
        return result.scalars().all()

    @staticmethod
    async def disconnect(db: AsyncSession, integration_id: str, user_id: str):
        integration = await db.get(Integration, integration_id)
        if not integration:
            raise NotFoundError("Integration not found")
        if str(integration.user_id) != user_id:
            raise PermissionDeniedError("Not your integration")
        await db.delete(integration)
        await db.commit()