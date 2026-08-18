
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..models.execution import Execution, ExecutionStatus
from ..models.agent import Agent
from ..utils.exceptions import PermissionDeniedError

class AnalyticsService:
    @staticmethod
    async def get_overview(db: AsyncSession, user_id: str):
        # Count total executions for user's agents
        total = await db.execute(
            select(func.count(Execution.id))
            .join(Agent)
            .where(Agent.owner_id == user_id)
        )
        failed = await db.execute(
            select(func.count(Execution.id))
            .join(Agent)
            .where(Agent.owner_id == user_id, Execution.status == ExecutionStatus.FAILED)
        )
        return {
            "total_executions": total.scalar() or 0,
            "failed_executions": failed.scalar() or 0,
        }

    @staticmethod
    async def get_agent_stats(db: AsyncSession, agent_id: str, user_id: str):
        # Verify ownership
        agent = await db.get(Agent, agent_id)
        if not agent or str(agent.owner_id) != user_id:
            raise PermissionDeniedError("Not your agent")
        total = await db.execute(
            select(func.count(Execution.id)).where(Execution.agent_id == agent_id)
        )
        avg_time = await db.execute(
            select(func.avg(Execution.completed_at - Execution.started_at))
            .where(Execution.agent_id == agent_id, Execution.status == ExecutionStatus.COMPLETED)
        )
        return {
            "agent_id": agent_id,
            "total_executions": total.scalar() or 0,
            "average_duration_seconds": avg_time.scalar() or 0,
        }