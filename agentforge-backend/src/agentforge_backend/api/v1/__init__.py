from fastapi import APIRouter
from .auth import router as auth_router
from .agents import router as agents_router
from .executions import router as executions_router
from .analytics import router as analytics_router
from .projects import router as projects_router
from .tasks import router as tasks_router
from .users import router as users_router
from .workspaces import router as workspaces_router
from .integrations import router as integrations_router
from .notifications import router as notifications_router
from .webhooks import router as webhooks_router
# New
from .settings import router as settings_router
from .permissions import router as permissions_router
from .tools import router as tools_router
from .activity import router as activity_router
from .health import router as health_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth")
router.include_router(users_router, prefix="/users")
router.include_router(workspaces_router, prefix="/workspaces")
router.include_router(projects_router, prefix="/projects")
router.include_router(tasks_router, prefix="/tasks")
router.include_router(agents_router, prefix="/agents")
router.include_router(executions_router, prefix="/executions")
router.include_router(analytics_router, prefix="/analytics")
router.include_router(integrations_router, prefix="/integrations")
router.include_router(notifications_router, prefix="/notifications")
router.include_router(webhooks_router, prefix="/webhooks")
router.include_router(tools_router, prefix="/tools")
router.include_router(permissions_router, prefix="/permissions")
router.include_router(activity_router, prefix="/activity")
router.include_router(settings_router, prefix="/settings")
router.include_router(health_router, prefix="/health")