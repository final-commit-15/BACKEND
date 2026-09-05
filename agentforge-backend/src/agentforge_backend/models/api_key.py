from sqlalchemy import String, ForeignKey, Boolean, DateTime, Index, UniqueConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from uuid import UUID
from datetime import datetime
from .base import TimestampMixin, SoftDeleteMixin, UUIDPrimaryKeyMixin


class ApiKey(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "api_keys"
    __table_args__ = (
        Index("ix_api_keys_user_id", "user_id"),
        Index("ix_api_keys_hashed_key", "hashed_key"),
        Index("ix_api_keys_expires_at", "expires_at"),
        Index("ix_api_keys_is_active", "is_active"),
        Index("ix_api_keys_deleted_at", "deleted_at"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    key_prefix: Mapped[str] = mapped_column(String(20), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_used_at: Mapped[datetime | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    scopes: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    workspace_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    last_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)

    user = relationship("User", back_populates="api_keys", foreign_keys="ApiKey.user_id")
    workspace = relationship("Workspace", foreign_keys="ApiKey.workspace_id")