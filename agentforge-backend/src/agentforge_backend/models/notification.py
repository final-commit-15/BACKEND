from sqlalchemy import String, Text, ForeignKey, Enum, Index, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from uuid import UUID
from datetime import datetime
from .base import TimestampMixin, SoftDeleteMixin, UUIDPrimaryKeyMixin
import enum


class NotificationType(str, enum.Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SYSTEM = "system"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    TASK_ASSIGNED = "task_assigned"
    TASK_COMPLETED = "task_completed"
    WORKSPACE_INVITATION = "workspace_invitation"
    AGENT_CREATED = "agent_created"
    AGENT_FAILED = "agent_failed"


class NotificationPriority(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Notification(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_id", "user_id"),
        Index("ix_notifications_type", "type"),
        Index("ix_notifications_is_read", "is_read"),
        Index("ix_notifications_created_at", "created_at"),
        Index("ix_notifications_deleted_at", "deleted_at"),
    )

    type: Mapped["NotificationType"] = mapped_column(
        Enum(NotificationType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
    priority: Mapped["NotificationPriority"] = mapped_column(
        Enum(NotificationPriority, values_callable=lambda x: [e.value for e in x]),
        default=NotificationPriority.NORMAL,
        nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    read_at: Mapped[datetime | None] = mapped_column(nullable=True)
    action_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    action_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    workspace_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    related_resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    related_resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    user = relationship("User", back_populates="notifications")
    workspace = relationship("Workspace", foreign_keys="Notification.workspace_id")