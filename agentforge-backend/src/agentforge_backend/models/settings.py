from sqlalchemy import String, Boolean, ForeignKey, JSON, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from uuid import UUID
from .base import TimestampMixin, UUIDPrimaryKeyMixin


class UserSettings(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User-level settings."""
    __tablename__ = "user_settings"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_settings_user"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    )
    theme: Mapped[str] = mapped_column(String(20), default="dark", nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    email_notifications: Mapped[bool] = mapped_column(default=True, nullable=False)
    push_notifications: Mapped[bool] = mapped_column(default=True, nullable=False)
    default_workspace_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True
    )
    preferences: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    user = relationship("User")
    default_workspace = relationship("Workspace", foreign_keys="UserSettings.default_workspace_id")