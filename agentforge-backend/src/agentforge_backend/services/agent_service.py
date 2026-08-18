from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.agent import Agent
from ..schemas.agent import AgentCreate, AgentUpdate
from ..utils.exceptions import NotFoundError, PermissionDeniedError
from uuid import UUID

class AgentService:
    @staticmethod
    async def create(db: AsyncSession, data: AgentCreate, owner_id: str) -> Agent:
        agent = Agent(**data.dict(), owner_id=owner_id)
        db.add(agent)
        await db.commit()
        await db.refresh(agent)
        return agent

    @staticmethod
    async def get_by_id(db: AsyncSession, agent_id: str) -> Agent | None:
        return await db.get(Agent, agent_id)

    @staticmethod
    async def list_by_owner(db: AsyncSession, owner_id: str):
        result = await db.execute(select(Agent).where(Agent.owner_id == owner_id))
        return result.scalars().all()

    @staticmethod
    async def update(db: AsyncSession, agent_id: str, data: AgentUpdate) -> Agent:
        agent = await db.get(Agent, agent_id)
        if not agent:
            raise NotFoundError("Agent not found")
        update_data = data.dict(exclude_unset=True)
        for k, v in update_data.items():
            setattr(agent, k, v)
        await db.commit()
        await db.refresh(agent)
        return agent

    @staticmethod
    async def delete(db: AsyncSession, agent_id: str) -> bool:
        agent = await db.get(Agent, agent_id)
        if not agent:
            return False
        await db.delete(agent)
        await db.commit()
        return True

    @staticmethod
    async def clone(db: AsyncSession, agent_id: str, owner_id: str) -> Agent:
        original = await db.get(Agent, agent_id)
        if not original:
            raise NotFoundError("Agent not found")
        clone_data = {c.name: getattr(original, c.name) for c in original.__table__.columns if c.name not in ("id", "owner_id", "created_at", "updated_at")}
        clone_data["name"] = f"{clone_data['name']} (clone)"
        agent = Agent(**clone_data, owner_id=owner_id)
        db.add(agent)
        await db.commit()
        await db.refresh(agent)
        return agent

    @staticmethod
    async def set_active(db: AsyncSession, agent_id: str, active: bool) -> Agent:
        agent = await db.get(Agent, agent_id)
        if not agent:
            raise NotFoundError("Agent not found")
        agent.is_active = active
        await db.commit()
        await db.refresh(agent)
        return agent