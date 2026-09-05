from __future__ import annotations

from sqlalchemy import String, Text, ForeignKey, Enum, Index, UniqueConstraint, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from uuid import UUID
from datetime import datetime
from .base import TimestampMixin, SoftDeleteMixin, UUIDPrimaryKeyMixin
import enum


class WorkspaceRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Workspace(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "workspaces"
    __table_args__ = (
        Index("ix_workspaces_owner_id", "owner_id"),
        Index("ix_workspaces_name", "name"),
        Index("ix_workspaces_deleted_at", "deleted_at"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    is_personal: Mapped[bool] = mapped_column(default=False, nullable=False)
    settings: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    owner = relationship("User", foreign_keys=[owner_id])
    projects = relationship("Project", back_populates="workspace", cascade="all, delete-orphan")
    members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")
    settings_obj = relationship("WorkspaceSettings", back_populates="workspace", uselist=False, cascade="all, delete-orphan")


class WorkspaceInvitation(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Workspace invitation tokens."""
    __tablename__ = "workspace_invitations"
    __table_args__ = (
        Index("ix_workspace_invitations_workspace_id", "workspace_id"),
        Index("ix_workspace_invitations_email", "email"),
        Index("ix_workspace_invitations_token_hash", "token_hash"),
        Index("ix_workspace_invitations_expires_at", "expires_at"),
    )

    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role: Mapped["WorkspaceRole"] = mapped_column(
        Enum(WorkspaceRole, values_callable=lambda x: [e.value for e in x]),
        default=WorkspaceRole.MEMBER,
        nullable=False
    )
    invited_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(nullable=False, index=True)
    accepted_at: Mapped[datetime | None] = mapped_column(nullable=True)
    accepted_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    workspace = relationship("Workspace")
    inviter = relationship("User", foreign_keys=[invited_by])
    acceptor = relationship("User", foreign_keys=[accepted_by])