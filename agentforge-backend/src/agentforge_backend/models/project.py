from __future__ import annotations

from sqlalchemy import String, Text, ForeignKey, Enum, Index, UniqueConstraint, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from uuid import UUID
from datetime import datetime
from .base import TimestampMixin, SoftDeleteMixin, UUIDPrimaryKeyMixin
import enum


class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Project(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "projects"
    __table_args__ = (
        Index("ix_projects_workspace_id", "workspace_id"),
        Index("ix_projects_owner_id", "owner_id"),
        Index("ix_projects_status", "status"),
        Index("ix_projects_deleted_at", "deleted_at"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    status: Mapped["ProjectStatus"] = mapped_column(
        Enum(ProjectStatus, values_callable=lambda x: [e.value for e in x]),
        default=ProjectStatus.ACTIVE,
        nullable=False
    )
    settings: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    workspace = relationship("Workspace", back_populates="projects")
    owner = relationship("User", foreign_keys=[owner_id])
    agents = relationship("Agent", back_populates="project")
    tasks = relationship("Task", back_populates="project")
    webhooks = relationship("Webhook", back_populates="project", foreign_keys="Webhook.project_id")