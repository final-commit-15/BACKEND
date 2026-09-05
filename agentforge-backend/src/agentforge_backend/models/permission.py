from sqlalchemy import String, ForeignKey, Enum, Index, UniqueConstraint, Table, Column, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from uuid import UUID
from datetime import datetime
from .base import TimestampMixin, UUIDPrimaryKeyMixin
import enum


class Permission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """System permissions for RBAC."""
    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint("resource", "action", name="uq_permission_resource_action"),
        Index("ix_permissions_resource", "resource"),
        Index("ix_permissions_action", "action"),
    )

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    resource: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)


class Role(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Roles for RBAC with workspace scoping."""
    __tablename__ = "roles"
    __table_args__ = (
        Index("ix_roles_workspace_id", "workspace_id"),
        Index("ix_roles_name", "name"),
        UniqueConstraint("workspace_id", "name", name="uq_role_workspace_name"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_system: Mapped[bool] = mapped_column(default=False, nullable=False)
    workspace_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    permissions = relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles"
    )
    workspace = relationship("Workspace", foreign_keys="Role.workspace_id")


# Association table for role-permissions many-to-many
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)

# Add back_populates to Permission
Permission.roles = relationship(
    "Role",
    secondary="role_permissions",
    back_populates="permissions"
)


class UserRoleAssignment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User role assignments with workspace scoping."""
    __tablename__ = "user_role_assignments"
    __table_args__ = (
        Index("ix_user_role_assignments_user_id", "user_id"),
        Index("ix_user_role_assignments_role_id", "role_id"),
        Index("ix_user_role_assignments_workspace_id", "workspace_id"),
        UniqueConstraint("user_id", "role_id", "workspace_id", name="uq_user_role_workspace"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    workspace_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    assigned_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    role = relationship("Role")
    workspace = relationship("Workspace", foreign_keys=[workspace_id])
    assigner = relationship("User", foreign_keys=[assigned_by])