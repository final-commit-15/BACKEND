from fastapi import Request, HTTPException, status, Depends
from typing import List, Optional
from ..security.permissions import user_has_permission
from ..models.user import User, UserRole
from ..middleware.auth import get_current_user_id
from ..db.session import async_session
from ..models.workspace_member import WorkspaceMember
from ..models.workspace import WorkspaceRole
from sqlalchemy import select
from uuid import UUID
from ..utils.exceptions import PermissionDeniedError


class RBACMiddleware:
    """Role-Based Access Control middleware."""
    
    def __init__(self, required_permission: str = None, required_roles: List[UserRole] = None):
        self.required_permission = required_permission
        self.required_roles = required_roles or []
    
    async def __call__(self, request: Request, user_id: str = Depends(get_current_user_id)):
        # Get user from database
        async with async_session() as db:
            from ..models.user import User
            result = await db.execute(select(User).where(User.id == UUID(user_id)))
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            
            # Check global role permissions
            if self.required_permission:
                if not user_has_permission(user.role, self.required_permission):
                    if user.role != UserRole.ADMIN:  # Admin bypasses permission checks
                        raise PermissionDeniedError(f"Permission required: {self.required_permission}")
            
            if self.required_roles:
                if user.role not in self.required_roles and user.role != UserRole.ADMIN:
                    raise PermissionDeniedError(f"Role required: {[r.value for r in self.required_roles]}")
            
            return user


def require_permission(permission: str):
    """Dependency to require a specific permission."""
    return RBACMiddleware(required_permission=permission)


def require_roles(*roles: UserRole):
    """Dependency to require one of the specified roles."""
    return RBACMiddleware(required_roles=list(roles))


def require_admin():
    """Dependency to require admin role."""
    return RBACMiddleware(required_roles=[UserRole.ADMIN])


async def require_workspace_permission(
    workspace_id: str,
    required_roles: List[WorkspaceRole],
    user_id: str = Depends(get_current_user_id),
) -> WorkspaceMember:
    """Check workspace-level permissions."""
    async with async_session() as db:
        result = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == UUID(workspace_id),
                WorkspaceMember.user_id == UUID(user_id),
            )
        )
        member = result.scalar_one_or_none()
        
        if not member:
            raise PermissionDeniedError("Not a member of this workspace")
        
        if member.role not in required_roles:
            raise PermissionDeniedError(f"Workspace role required: {[r.value for r in required_roles]}")
        
        return member


def workspace_member_required(*roles: WorkspaceRole):
    """Dependency factory for workspace membership checks."""
    async def check_workspace_access(
        workspace_id: str,
        user_id: str = Depends(get_current_user_id),
    ) -> WorkspaceMember:
        return await require_workspace_permission(workspace_id, list(roles), user_id)
    return check_workspace_access


async def get_workspace_role(workspace_id: str, user_id: str) -> Optional[WorkspaceRole]:
    """Get user's role in a workspace."""
    async with async_session() as db:
        result = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == UUID(workspace_id),
                WorkspaceMember.user_id == UUID(user_id),
            )
        )
        member = result.scalar_one_or_none()
        return member.role if member else None