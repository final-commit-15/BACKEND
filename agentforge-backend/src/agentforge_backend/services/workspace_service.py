from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.workspace import Workspace, WorkspaceRole
from ..models.workspace_member import WorkspaceMember
from ..models.user import User
from ..schemas.workspace import WorkspaceCreate, WorkspaceMemberAdd
from ..utils.exceptions import NotFoundError, PermissionDeniedError

class WorkspaceService:
    @staticmethod
    async def create(db: AsyncSession, data: WorkspaceCreate, owner_id: str) -> Workspace:
        workspace = Workspace(name=data.name, description=data.description, owner_id=owner_id)
        db.add(workspace)
        await db.flush()
        member = WorkspaceMember(user_id=owner_id, workspace_id=workspace.id, role=WorkspaceRole.OWNER)
        db.add(member)
        await db.commit()
        await db.refresh(workspace)
        return workspace

    @staticmethod
    async def get_by_id(db: AsyncSession, workspace_id: str) -> Workspace | None:
        return await db.get(Workspace, workspace_id)

    @staticmethod
    async def list_by_user(db: AsyncSession, user_id: str):
        stmt = select(Workspace).join(WorkspaceMember).where(WorkspaceMember.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def add_member(db: AsyncSession, workspace_id: str, data: WorkspaceMemberAdd, acting_user_id: str) -> WorkspaceMember:
        actor = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == acting_user_id
            )
        )
        actor_member = actor.scalar_one_or_none()
        if not actor_member or actor_member.role not in (WorkspaceRole.OWNER, WorkspaceRole.ADMIN):
            raise PermissionDeniedError("Only owners/admins can add members")

        user = await db.get(User, data.user_id)
        if not user:
            raise NotFoundError("User not found")

        # Check if already a member
        existing = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == data.user_id
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError("User is already a member")

        member = WorkspaceMember(user_id=data.user_id, workspace_id=workspace_id, role=data.role)
        db.add(member)
        await db.commit()
        await db.refresh(member)
        return member