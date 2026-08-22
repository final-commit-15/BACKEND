from xmlrpc import client

from agentforge_backend import db
from ..models.task import Task
from agentforge_backend.db.session import AsyncSessionLocal
from agentforge_backend.schemas import agent, task
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.execution import Execution, ExecutionStatus
from ..models.execution_log import ExecutionLog, LogSeverity
from ..models.agent import Agent
from ..clients.agents import AgentsClient
from ..websocket.manager import ws_manager
from ..utils.exceptions import NotFoundError, PermissionDeniedError
from uuid import uuid4
import asyncio
from datetime import datetime
from sqlalchemy import select
from ..models.task import Task


class ExecutionService:
    @staticmethod
    async def start(db: AsyncSession, agent_id: str, task_id: str | None, input_data: dict, user_id: str) -> Execution:
       
     # verify agent exists and belongs to user (or user has access)
        agent = await db.get(Agent, agent_id)
        if not agent:
            raise NotFoundError("Agent not found")

        if not agent.is_active:
            raise PermissionDeniedError("Agent is disabled")

        if str(agent.owner_id) != user_id:
            # TODO: check workspace permissions
            raise PermissionDeniedError("Access denied")

        if task_id:
            task = await db.get(Task, task_id)
            if not task:
                raise NotFoundError("Task not found")

        execution = Execution(
            id=uuid4(),
            agent_id=agent_id,
            task_id=task_id,
            input=input_data,
            status=ExecutionStatus.QUEUED
        )
        db.add(execution)
        await db.commit()
        await db.refresh(execution)
        # Queue to background worker (Celery) or run async
        from ..workers.execution_worker import run_execution_task
        run_execution_task.delay(str(execution.id))
        await ws_manager.broadcast(str(execution.id), {"status": "queued"})
        return execution

    @staticmethod
    async def list_by_user(db: AsyncSession, user_id: str, limit: int = 10):
        result = await db.execute(
            select(Execution)
            .join(Task, Execution.task_id == Task.id)
            .where(Task.assignee_id == user_id)
            .order_by(Execution.created_at.desc())
            .limit(limit)
        )

        return result.scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, execution_id: str) -> Execution | None:
        return await db.get(Execution, execution_id)

    @staticmethod
    async def _run(execution_id: str):
        from ..db.session import AsyncSessionLocal

    # ---------------------------------------------------------
    # 1. Read execution + agent and mark execution as RUNNING
    # ---------------------------------------------------------
        async with AsyncSessionLocal() as db:
            execution = await db.get(Execution, execution_id)

            if not execution:
                return

            agent = await db.get(Agent, execution.agent_id)

            if not agent:
                execution.status = ExecutionStatus.FAILED
                execution.error = "Agent not found"
                execution.completed_at = datetime.utcnow()
                await db.commit()
                return

            config = {
                "name": agent.name,
                "type": agent.agent_type,
                "system_prompt": agent.system_prompt,
                "model": agent.model,
                "temperature": agent.temperature,
                "max_tokens": agent.max_tokens,
                "tools": agent.tools,
                "permissions": agent.permissions,
                "memory": agent.memory,
                "execution_limits": agent.execution_limits,
                "timeout": agent.timeout_seconds,
                "retry_policy": agent.retry_policy,
            }

            input_data = execution.input

            execution.status = ExecutionStatus.RUNNING
            execution.started_at = datetime.utcnow()

            await db.commit()

            execution_id_str = str(execution.id)

        await ws_manager.broadcast(
            execution_id_str,
            {"status": "running"},
        )

    # ---------------------------------------------------------
    # 2. Call AGENTS WITHOUT holding a DB session
    # ---------------------------------------------------------
        try:
            client = AgentsClient()

            agents_agent_id = f"{agent.agent_type}_agent"

            result = await client.execute(
                agents_agent_id,
                input_data,
            )

        except Exception as e:
        # -----------------------------------------------------
        # 3. Open a NEW DB session to save failure
        # -----------------------------------------------------
            async with AsyncSessionLocal() as db:
                execution = await db.get(Execution, execution_id)

                if execution:
                    execution.status = ExecutionStatus.FAILED
                    execution.error = str(e)
                    execution.completed_at = datetime.utcnow()
                    await db.commit()

            await ws_manager.broadcast(
                execution_id_str,
                {
                    "status": "failed",
                    "error": str(e),
                },
            )
            return

    # ---------------------------------------------------------
    # 4. Open a NEW DB session to save success
    # ---------------------------------------------------------
        async with AsyncSessionLocal() as db:
            execution = await db.get(Execution, execution_id)

            if execution:
                execution.status = ExecutionStatus.COMPLETED
                execution.output = result
                execution.completed_at = datetime.utcnow()

                await db.commit()

        await ws_manager.broadcast(
            execution_id_str,
            {
                "status": "completed",
                "output": result,
            },
        )