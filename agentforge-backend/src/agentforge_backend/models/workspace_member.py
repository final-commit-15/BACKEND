from __future__ import annotations

from sqlalchemy import ForeignKey, Enum as SQLEnum, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from uuid import UUID
from datetime import datetime
from .workspace import WorkspaceRole
from .base import TimestampMixin, SoftDeleteMixin, UUIDPrimaryKeyMixin


class WorkspaceMember(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "workspace_members"
    __table_args__ = (
        Index("ix_workspace_members_workspace_id", "workspace_id"),
        Index("ix_workspace_members_user_id", "user_id"),
        Index("ix_workspace_members_role", "role"),
        UniqueConstraint("user_id", "workspace_id", name="uq_workspace_member_user_workspace"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role: Mapped["WorkspaceRole"] = mapped_column(
        SQLEnum(WorkspaceRole),
        default=WorkspaceRole.MEMBER,
        nullable=False
    )
    invited_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    invited_at: Mapped[datetime | None] = mapped_column(nullable=True)
    joined_at: Mapped[datetime | None] = mapped_column(nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    workspace = relationship("Workspace", back_populates="members")
    inviter = relationship("User", foreign_keys=[invited_by])