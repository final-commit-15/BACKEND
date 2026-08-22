from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID, uuid4
from .base import Base

class Tool(Base):
    __tablename__ = "tools"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(500))
    version: Mapped[str] = mapped_column(String(20), default="1.0.0")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)