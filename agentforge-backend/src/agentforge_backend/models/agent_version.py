from sqlalchemy import String, Text, JSON, ForeignKey, Integer, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from uuid import UUID
from datetime import datetime
from .base import TimestampMixin, UUIDPrimaryKeyMixin


class AgentVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "agent_versions"
    __table_args__ = (
        Index("ix_agent_versions_agent_id", "agent_id"),
        Index("ix_agent_versions_version_number", "version_number"),
        UniqueConstraint("agent_id", "version_number", name="uq_agent_version_number"),
    )

    agent_id: Mapped[UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    version_number: Mapped[int] = mapped_column(nullable=False)
    config_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    agent = relationship("Agent", back_populates="versions")
    creator = relationship("User", foreign_keys=[created_by])