from sqlalchemy import String, Text, JSON, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base import Base
from uuid import UUID

class AgentVersion(Base):
    __tablename__ = "agent_versions"
    version_number: Mapped[int] = mapped_column(Integer)
    config_snapshot: Mapped[dict] = mapped_column(JSON)
    agent_id: Mapped[UUID] = mapped_column(ForeignKey("agents.id"))

    agent = relationship("Agent", back_populates="versions")