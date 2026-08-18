from .celery_app import celery_app
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.session import AsyncSessionLocal
from ..services.execution_service import ExecutionService

@celery_app.task(name="run_execution")
def run_execution_task(execution_id: str):
    import asyncio
    async def _run():
        async with AsyncSessionLocal() as db:
            await ExecutionService._run(db, execution_id)
    asyncio.run(_run())