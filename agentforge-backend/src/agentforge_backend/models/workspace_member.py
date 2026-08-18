from sqlalchemy import ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base import Base
from uuid import UUID
from .workspace import WorkspaceRole

class WorkspaceMember(Base):
    __tablename__ = "workspace_members"
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id"), primary_key=True)
    role: Mapped[WorkspaceRole] = mapped_column(SQLEnum(WorkspaceRole), default=WorkspaceRole.MEMBER)

    user = relationship("User")
    workspace = relationship("Workspace", back_populates="members")

    __table_args__ = (UniqueConstraint("user_id", "workspace_id"),)