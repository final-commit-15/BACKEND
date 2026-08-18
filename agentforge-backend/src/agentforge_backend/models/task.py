from sqlalchemy import String, Text, ForeignKey, Enum, Integer, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base import Base
from uuid import UUID
from datetime import datetime
import enum

class TaskStatus(str, enum.Enum):
    TODO = "todo"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Task(Base):
    __tablename__ = "tasks"
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.TODO)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    dependencies: Mapped[list] = mapped_column(JSON, default=list)
    result: Mapped[dict] = mapped_column(JSON, nullable=True)
    assignee_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=True)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), nullable=True)

    assignee = relationship("User", back_populates="tasks")
    executions = relationship("Execution", back_populates="task")
    project = relationship("Project", back_populates="tasks")