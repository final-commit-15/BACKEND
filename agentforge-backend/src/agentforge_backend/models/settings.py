from sqlalchemy import String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID, uuid4
from .base import Base  # your declarative base

class WorkspaceSettings(Base):
    __tablename__ = "workspace_settings"

    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id"), primary_key=True)
    theme: Mapped[str] = mapped_column(String(20), default="dark")
    language: Mapped[str] = mapped_column(String(10), default="en")
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Kolkata")
    notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_save: Mapped[bool] = mapped_column(Boolean, default=True)
    default_model: Mapped[str] = mapped_column(String(50), default="gpt-5")