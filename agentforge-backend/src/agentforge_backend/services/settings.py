from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID
from typing import Optional, Dict, Any
from ..models.settings import WorkspaceSettings

class SettingsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_workspace_settings(self, workspace_id: UUID) -> Optional[Dict[str, Any]]:
        stmt = select(WorkspaceSettings).where(WorkspaceSettings.workspace_id == workspace_id)
        result = await self.db.execute(stmt)
        settings = result.scalar_one_or_none()
        if not settings:
            return None
        return {
            "workspace_id": str(settings.workspace_id),
            "theme": settings.theme,
            "language": settings.language,
            "timezone": settings.timezone,
            "notifications": settings.notifications,
            "auto_save": settings.auto_save,
            "default_model": settings.default_model,
        }

    async def update_workspace_settings(self, workspace_id: UUID, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # Check if exists
        stmt = select(WorkspaceSettings).where(WorkspaceSettings.workspace_id == workspace_id)
        result = await self.db.execute(stmt)
        settings = result.scalar_one_or_none()
        if not settings:
            # Create if missing (optional)
            settings = WorkspaceSettings(workspace_id=workspace_id)
            self.db.add(settings)
            await self.db.flush()

        # Update fields
        for key, value in data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        await self.db.commit()
        await self.db.refresh(settings)
        return await self.get_workspace_settings(workspace_id)