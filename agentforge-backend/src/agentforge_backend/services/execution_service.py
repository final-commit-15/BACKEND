from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.execution import Execution, ExecutionStatus
from ..models.execution_log import ExecutionLog, LogSeverity
from ..models.agent import Agent
from ..clients.agents import AgentsClient
from ..websocket.manager import ws_manager
from ..utils.exceptions import NotFoundError
from uuid import uuid4
import asyncio
from datetime import datetime

class ExecutionService:
    @staticmethod
    async def start(db: AsyncSession, agent_id: str, task_id: str | None, input_data: dict, user_id: str) -> Execution:
        # verify agent exists and belongs to user (or user has access)
        agent = await db.get(Agent, agent_id)
        if not agent:
            raise NotFoundError("Agent not found")
        if str(agent.owner_id) != user_id:
            # TODO: check workspace permissions
            pass

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
    async def get_by_id(db: AsyncSession, execution_id: str) -> Execution | None:
        return await db.get(Execution, execution_id)

    @staticmethod
    async def _run(db: AsyncSession, execution_id: str):
        # This method is called by the worker
        execution = await db.get(Execution, execution_id)
        if not execution:
            return
        agent = await db.get(Agent, execution.agent_id)
        if not agent:
            execution.status = ExecutionStatus.FAILED
            execution.error = "Agent not found"
            await db.commit()
            return

        # Prepare agent config
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
        try:
            execution.status = ExecutionStatus.RUNNING
            execution.started_at = datetime.utcnow()
            await db.commit()
            await ws_manager.broadcast(str(execution.id), {"status": "running"})

            # Call agent service
            client = AgentsClient()
            result = await client.execute(config, execution.input)

            execution.status = ExecutionStatus.COMPLETED
            execution.output = result
            execution.completed_at = datetime.utcnow()
            await db.commit()
            await ws_manager.broadcast(str(execution.id), {"status": "completed", "output": result})
        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.utcnow()
            await db.commit()
            await ws_manager.broadcast(str(execution.id), {"status": "failed", "error": str(e)})