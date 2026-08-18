from celery import Celery
from ..config.settings import settings

celery_app = Celery(
    "agentforge_backend",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["agentforge_backend.workers.execution_worker",
             "agentforge_backend.workers.webhook_worker",
             "agentforge_backend.workers.notification_worker"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)