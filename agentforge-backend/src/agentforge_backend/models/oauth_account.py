from sqlalchemy import String, ForeignKey, Text, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from uuid import UUID
from datetime import datetime
from .base import TimestampMixin, SoftDeleteMixin, UUIDPrimaryKeyMixin


class OAuthAccount(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "oauth_accounts"
    __table_args__ = (
        Index("ix_oauth_accounts_user_id", "user_id"),
        Index("ix_oauth_accounts_provider", "provider"),
        Index("ix_oauth_accounts_provider_user_id", "provider_user_id"),
        Index("ix_oauth_accounts_deleted_at", "deleted_at"),
        UniqueConstraint("provider", "provider_user_id", name="uq_oauth_account_provider_user"),
    )

    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_type: Mapped[str] = mapped_column(String(50), default="Bearer", nullable=False)
    scope: Mapped[str | None] = mapped_column(String(500), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(nullable=True)
    id_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    user = relationship("User", back_populates="oauth_accounts")