from sqlalchemy import String, Text, JSON, Boolean, ForeignKey, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base import Base
from uuid import UUID

class Agent(Base):
    __tablename__ = "agents"
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    agent_type: Mapped[str] = mapped_column(String(100))
    system_prompt: Mapped[str] = mapped_column(Text, nullable=True)
    model: Mapped[str] = mapped_column(String(100))
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, default=4096)
    tools: Mapped[list] = mapped_column(JSON, default=list)
    permissions: Mapped[dict] = mapped_column(JSON, default=dict)
    memory: Mapped[dict] = mapped_column(JSON, default=dict)
    execution_limits: Mapped[dict] = mapped_column(JSON, default=dict)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=60)
    retry_policy: Mapped[dict] = mapped_column(JSON, default={"max_retries": 3})
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), nullable=True)

    owner = relationship("User", back_populates="agents")
    executions = relationship("Execution", back_populates="agent")
    versions = relationship("AgentVersion", back_populates="agent")
    project = relationship("Project", back_populates="agents")