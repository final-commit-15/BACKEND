from sqlalchemy import String, JSON, ForeignKey, Enum, DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base import Base
from uuid import UUID
from datetime import datetime
import enum

class ExecutionStatus(str, enum.Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class Execution(Base):
    __tablename__ = "executions"
    status: Mapped[ExecutionStatus] = mapped_column(Enum(ExecutionStatus), default=ExecutionStatus.PENDING)
    input: Mapped[dict] = mapped_column(JSON)
    output: Mapped[dict] = mapped_column(JSON, nullable=True)
    error: Mapped[str] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    agent_id: Mapped[UUID] = mapped_column(ForeignKey("agents.id"))
    task_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id"), nullable=True)

    agent = relationship("Agent", back_populates="executions")
    task = relationship("Task", back_populates="executions")
    logs = relationship("ExecutionLog", back_populates="execution")