from __future__ import annotations

from sqlalchemy import String, Text, ForeignKey, Enum, Integer, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from uuid import UUID
from .base import TimestampMixin, UUIDPrimaryKeyMixin
import enum


class LogSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"


class ExecutionLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "execution_logs"
    __table_args__ = (
        Index("ix_execution_logs_execution_id", "execution_id"),
        Index("ix_execution_logs_severity", "severity"),
        Index("ix_execution_logs_event_type", "event_type"),
    )

    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="info", nullable=False, index=True)
    tool_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    execution_id: Mapped[UUID] = mapped_column(
        ForeignKey("executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    execution = relationship("Execution", back_populates="logs")