from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.project import Project
from ..models.workspace_member import WorkspaceMember
from ..schemas.project import ProjectCreate
from ..utils.exceptions import NotFoundError, PermissionDeniedError

class ProjectService:
    @staticmethod
    async def create(db: AsyncSession, data: ProjectCreate, user_id: str) -> Project:
        # Verify user is a member of the workspace
        member = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == data.workspace_id,
                WorkspaceMember.user_id == user_id
            )
        )
        if not member.scalar_one_or_none():
            raise PermissionDeniedError("User is not a member of this workspace")
        project = Project(name=data.name, description=data.description, workspace_id=data.workspace_id)
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project

    @staticmethod
    async def get_by_id(db: AsyncSession, project_id: str) -> Project | None:
        return await db.get(Project, project_id)

    @staticmethod
    async def list_by_workspace(db: AsyncSession, workspace_id: str):
        result = await db.execute(select(Project).where(Project.workspace_id == workspace_id))
        return result.scalars().all()