from sqlalchemy import String, Text, JSON, Boolean, ForeignKey, Enum, Index, UniqueConstraint, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from uuid import UUID
from datetime import datetime
from .base import TimestampMixin, SoftDeleteMixin, UUIDPrimaryKeyMixin
import enum


class AgentStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Agent(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "agents"
    __table_args__ = (
        Index("ix_agents_owner_id", "owner_id"),
        Index("ix_agents_project_id", "project_id"),
        Index("ix_agents_status", "status"),
        Index("ix_agents_agent_type", "agent_type"),
        Index("ix_agents_deleted_at", "deleted_at"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    temperature: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    max_tokens: Mapped[int] = mapped_column(Integer, default=4096, nullable=False)
    tools: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    permissions: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    memory: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    execution_limits: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    retry_policy: Mapped[dict] = mapped_column(JSON, default={"max_retries": 3}, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped["AgentStatus"] = mapped_column(
        Enum(AgentStatus, values_callable=lambda x: [e.value for e in x]),
        default=AgentStatus.ACTIVE,
        nullable=False
    )
    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    owner = relationship("User", back_populates="agents", foreign_keys="Agent.owner_id")
    executions = relationship("Execution", back_populates="agent")
    versions = relationship("AgentVersion", back_populates="agent", cascade="all, delete-orphan")
    project = relationship("Project", back_populates="agents")