from sqlalchemy import String, Text, JSON, ForeignKey, Enum, Index, Integer, DateTime, Text as TextType
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from uuid import UUID
from datetime import datetime
from .base import TimestampMixin, SoftDeleteMixin, UUIDPrimaryKeyMixin
import enum


class ExecutionStatus(str, enum.Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class Execution(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "executions"
    __table_args__ = (
        Index("ix_executions_agent_id", "agent_id"),
        Index("ix_executions_task_id", "task_id"),
        Index("ix_executions_status", "status"),
        Index("ix_executions_started_at", "started_at"),
        Index("ix_executions_completed_at", "completed_at"),
        Index("ix_executions_deleted_at", "deleted_at"),
    )

    status: Mapped["ExecutionStatus"] = mapped_column(
        Enum(ExecutionStatus, values_callable=lambda x: [e.value for e in x]),
        default=ExecutionStatus.PENDING,
        nullable=False,
        index=True
    )
    input: Mapped[dict] = mapped_column(JSON, nullable=False)
    output: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    agent_id: Mapped[UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    task_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    triggered_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    agent = relationship("Agent", back_populates="executions")
    task = relationship("Task", back_populates="executions")
    trigger_user = relationship("User", foreign_keys="Execution.triggered_by")
    logs = relationship("ExecutionLog", back_populates="execution", cascade="all, delete-orphan")
    events = relationship("ExecutionEvent", back_populates="execution", cascade="all, delete-orphan")
    metrics = relationship("ExecutionMetric", back_populates="execution", cascade="all, delete-orphan")


class ExecutionEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Detailed execution events for streaming/debugging."""
    __tablename__ = "execution_events"
    __table_args__ = (
        Index("ix_execution_events_execution_id", "execution_id"),
        Index("ix_execution_events_event_type", "event_type"),
    )

    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    execution_id: Mapped[UUID] = mapped_column(
        ForeignKey("executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    execution = relationship("Execution", back_populates="events")


class ExecutionMetric(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Execution metrics for analytics."""
    __tablename__ = "execution_metrics"
    __table_args__ = (
        Index("ix_execution_metrics_execution_id", "execution_id"),
        Index("ix_execution_metrics_metric_name", "metric_name"),
    )

    metric_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    metric_value: Mapped[float] = mapped_column(nullable=False)
    metric_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    execution_id: Mapped[UUID] = mapped_column(
        ForeignKey("executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    execution = relationship("Execution", back_populates="metrics")


class ScheduledExecution(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Scheduled/recurring executions."""
    __tablename__ = "scheduled_executions"
    __table_args__ = (
        Index("ix_scheduled_executions_agent_id", "agent_id"),
        Index("ix_scheduled_executions_next_run", "next_run_at"),
        Index("ix_scheduled_executions_enabled", "enabled"),
        Index("ix_scheduled_executions_deleted_at", "deleted_at"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    agent_id: Mapped[UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    input_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    enabled: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_run_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    run_count: Mapped[int] = mapped_column(default=0, nullable=False)
    created_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    agent = relationship("Agent")
    creator = relationship("User", foreign_keys=[created_by])