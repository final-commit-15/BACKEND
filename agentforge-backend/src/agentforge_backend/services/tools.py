from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from uuid import UUID
from typing import List, Dict, Any, Optional
from ..models.tools import Tool

class ToolsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_tools(self, workspace_id: UUID) -> List[Dict[str, Any]]:
        stmt = select(Tool).where(Tool.workspace_id == workspace_id)
        result = await self.db.execute(stmt)
        tools = result.scalars().all()
        return [{
            "id": str(t.id),
            "name": t.name,
            "category": t.category,
            "description": t.description,
            "version": t.version,
            "enabled": t.enabled,
        } for t in tools]

    async def create_tool(self, data: Dict[str, Any], workspace_id: UUID) -> Dict[str, Any]:
        tool = Tool(
            workspace_id=workspace_id,
            name=data["name"],
            category=data["category"],
            description=data["description"],
            version=data.get("version", "1.0.0"),
            enabled=True,
        )
        self.db.add(tool)
        await self.db.commit()
        await self.db.refresh(tool)
        return {
            "id": str(tool.id),
            "name": tool.name,
            "category": tool.category,
            "description": tool.description,
            "version": tool.version,
            "enabled": tool.enabled,
        }

    async def update_tool(self, tool_id: UUID, data: Dict[str, Any], workspace_id: UUID) -> Optional[Dict[str, Any]]:
        stmt = select(Tool).where(Tool.id == tool_id, Tool.workspace_id == workspace_id)
        result = await self.db.execute(stmt)
        tool = result.scalar_one_or_none()
        if not tool:
            return None
        for key, value in data.items():
            if hasattr(tool, key):
                setattr(tool, key, value)
        await self.db.commit()
        await self.db.refresh(tool)
        return {
            "id": str(tool.id),
            "name": tool.name,
            "category": tool.category,
            "description": tool.description,
            "version": tool.version,
            "enabled": tool.enabled,
        }

    async def delete_tool(self, tool_id: UUID, workspace_id: UUID) -> bool:
        stmt = select(Tool).where(Tool.id == tool_id, Tool.workspace_id == workspace_id)
        result = await self.db.execute(stmt)
        tool = result.scalar_one_or_none()
        if not tool:
            return False
        await self.db.delete(tool)
        await self.db.commit()
        return True