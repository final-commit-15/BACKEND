from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base import Base
from uuid import UUID

class Project(Base):
    __tablename__ = "projects"
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id"), nullable=False)

    # Relationships
    workspace = relationship("Workspace", back_populates="projects")
    agents = relationship("Agent", back_populates="project")
    tasks = relationship("Task", back_populates="project")