from .celery_app import celery_app
from ..services.execution_service import ExecutionService


@celery_app.task(name="run_execution")
def run_execution_task(execution_id: str):
    import asyncio

    async def _run():
        await ExecutionService._run(execution_id)

    asyncio.run(_run())