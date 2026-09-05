from __future__ import annotations

from sqlalchemy import String, Boolean, ForeignKey, JSON, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from uuid import UUID
from .base import TimestampMixin, UUIDPrimaryKeyMixin


class WorkspaceSettings(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Workspace-level settings."""
    __tablename__ = "workspace_settings"
    __table_args__ = (
        UniqueConstraint("workspace_id", name="uq_workspace_settings_workspace"),
    )

    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    )
    theme: Mapped[str] = mapped_column(String(20), default="dark", nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_save: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    default_model: Mapped[str] = mapped_column(String(50), default="gpt-4", nullable=False)
    ai_settings: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    security_settings: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    notification_settings: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    workspace = relationship("Workspace", back_populates="settings_obj")