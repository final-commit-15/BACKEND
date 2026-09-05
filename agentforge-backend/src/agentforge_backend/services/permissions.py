from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from uuid import UUID
from typing import List, Dict, Any
from ..models.permission import Permission, Role
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any

class PermissionsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_permissions(self) -> List[Dict[str, Any]]:
        stmt = select(Permission)
        result = await self.db.execute(stmt)
        perms = result.scalars().all()
        return [{"id": str(p.id), "name": p.name, "description": p.description} for p in perms]

    async def get_all_roles(self) -> List[Dict[str, Any]]:
        stmt = select(Role).options(selectinload(Role.permissions))
        result = await self.db.execute(stmt)
        roles = result.scalars().all()
        return [{
            "id": str(r.id),
            "name": r.name,
            "description": r.description,
            "permissions": [{"id": str(p.id), "name": p.name} for p in r.permissions]
        } for r in roles]

    async def create_role(self, data: Dict[str, Any]) -> Dict[str, Any]:
        role = Role(name=data["name"], description=data.get("description"))
        if "permissions" in data and data["permissions"]:
            perm_ids = [UUID(x) for x in data["permissions"]]
            stmt = select(Permission).where(Permission.id.in_(perm_ids))
            result = await self.db.execute(stmt)
            role.permissions = result.scalars().all()
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        return await self.get_role(role.id)

    async def update_role(self, role_id: UUID, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        stmt = select(Role).where(Role.id == role_id)
        result = await self.db.execute(stmt)
        role = result.scalar_one_or_none()
        if not role:
            return None
        if "name" in data:
            role.name = data["name"]
        if "description" in data:
            role.description = data["description"]
        if "permissions" in data:
            perm_ids = [UUID(x) for x in data["permissions"]]
            stmt = select(Permission).where(Permission.id.in_(perm_ids))
            result = await self.db.execute(stmt)
            role.permissions = result.scalars().all()
        await self.db.commit()
        await self.db.refresh(role)
        return await self.get_role(role.id)