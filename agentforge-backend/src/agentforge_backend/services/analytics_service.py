
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..models.execution import Execution, ExecutionStatus
from ..models.agent import Agent
from ..utils.exceptions import PermissionDeniedError
from datetime import datetime, timedelta
from sqlalchemy import select, func

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


    @staticmethod
    async def execution_activity(db: AsyncSession, range: str, user_id: str):
        days = {"24h": 1, "7d": 7, "30d": 30, "90d": 90}.get(range, 7)
        since = datetime.utcnow() - timedelta(days=days)

        result = await db.execute(
            select(
                func.date(Execution.created_at).label("date"),
                func.count(Execution.id).label("count"),
            )
            .join(Agent)
            .where(
                Agent.owner_id == user_id,
                Execution.created_at >= since,
            )
            .group_by(func.date(Execution.created_at))
            .order_by(func.date(Execution.created_at))
        )

        return [
            {"date": str(row.date), "count": row.count}
            for row in result.all()
        ]

    @staticmethod
    async def agent_usage(db: AsyncSession, range: str, user_id: str):
        days = {"24h": 1, "7d": 7, "30d": 30, "90d": 90}.get(range, 7)
        since = datetime.utcnow() - timedelta(days=days)

        result = await db.execute(
            select(
                Agent.name,
                func.count(Execution.id).label("executions"),
            )
            .join(Execution)
            .where(
                Agent.owner_id == user_id,
                Execution.created_at >= since,
            )
            .group_by(Agent.name)
            .order_by(func.count(Execution.id).desc())
        )

        return [
            {"agent": row.name, "executions": row.executions}
            for row in result.all()
        ]

    @staticmethod
    async def tasks_over_time(db: AsyncSession, range: str, user_id: str):
        # Temporary implementation until task analytics are added
        return []

    @staticmethod
    async def agent_performance(db: AsyncSession, range: str, user_id: str):
        days = {"24h": 1, "7d": 7, "30d": 30, "90d": 90}.get(range, 7)
        since = datetime.utcnow() - timedelta(days=days)

        result = await db.execute(
            select(
                Agent.name,
                func.count(Execution.id).label("total"),
                func.count().filter(
                    Execution.status == ExecutionStatus.COMPLETED
                ).label("completed"),
            )
            .join(Execution)
            .where(
                Agent.owner_id == user_id,
                Execution.created_at >= since,
            )
            .group_by(Agent.name)
        )

        return [
            {
                "agent": row.name,
                "total": row.total,
                "completed": row.completed,
                "success_rate": round(
                    (row.completed / row.total * 100) if row.total else 0,
                    2,
                ),
            }
            for row in result.all()
        ]