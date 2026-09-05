from sqlalchemy import String, Text, ForeignKey, Enum, Index, Integer, DateTime, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from uuid import UUID
from datetime import datetime
from .base import TimestampMixin, SoftDeleteMixin, UUIDPrimaryKeyMixin
import enum


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Task(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_project_id", "project_id"),
        Index("ix_tasks_assignee_id", "assignee_id"),
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_priority", "priority"),
        Index("ix_tasks_deadline", "deadline"),
        Index("ix_tasks_deleted_at", "deleted_at"),
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped["TaskStatus"] = mapped_column(
        Enum(TaskStatus, values_callable=lambda x: [e.value for e in x]),
        default=TaskStatus.TODO,
        nullable=False,
        index=True
    )
    priority: Mapped["TaskPriority"] = mapped_column(
        Enum(TaskPriority, values_callable=lambda x: [e.value for e in x]),
        default=TaskPriority.MEDIUM,
        nullable=False,
        index=True
    )
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    dependencies: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    assignee_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    created_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    assignee = relationship("User", back_populates="tasks", foreign_keys="Task.assignee_id")
    creator = relationship("User", foreign_keys="Task.created_by")
    project = relationship("Project", back_populates="tasks")
    executions = relationship("Execution", back_populates="task")
    attachments = relationship("TaskAttachment", back_populates="task", cascade="all, delete-orphan")
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan")


class TaskAttachment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "task_attachments"
    __table_args__ = (
        Index("ix_task_attachments_task_id", "task_id"),
    )

    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    uploaded_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    task = relationship("Task", back_populates="attachments")
    uploader = relationship("User", foreign_keys="TaskAttachment.uploaded_by")


class TaskComment(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "task_comments"
    __table_args__ = (
        Index("ix_task_comments_task_id", "task_id"),
        Index("ix_task_comments_user_id", "user_id"),
    )

    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    parent_comment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("task_comments.id", ondelete="CASCADE"),
        nullable=True
    )

    task = relationship("Task", back_populates="comments")
    user = relationship("User", foreign_keys="TaskComment.user_id")
    parent = relationship("TaskComment", remote_side="TaskComment.id", backref="replies")