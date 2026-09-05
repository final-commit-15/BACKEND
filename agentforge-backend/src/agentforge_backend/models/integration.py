from sqlalchemy import String, Text, ForeignKey, JSON, Boolean, Index, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from uuid import UUID
from datetime import datetime
from .base import TimestampMixin, SoftDeleteMixin, UUIDPrimaryKeyMixin
import enum


class IntegrationStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    EXPIRED = "expired"


class IntegrationProvider(str, enum.Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
    SLACK = "slack"
    DISCORD = "discord"
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    CUSTOM = "custom"


class Integration(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "integrations"
    __table_args__ = (
        Index("ix_integrations_user_id", "user_id"),
        Index("ix_integrations_provider", "provider"),
        Index("ix_integrations_status", "status"),
        Index("ix_integrations_deleted_at", "deleted_at"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped["IntegrationProvider"] = mapped_column(
        Enum(IntegrationProvider, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
    encrypted_credentials: Mapped[str] = mapped_column(Text, nullable=False)
    config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped["IntegrationStatus"] = mapped_column(
        Enum(IntegrationStatus, values_callable=lambda x: [e.value for e in x]),
        default=IntegrationStatus.ACTIVE,
        nullable=False,
        index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_sync_at: Mapped[datetime | None] = mapped_column(nullable=True)
    last_sync_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    config_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    user = relationship("User", back_populates="integrations")
    workspace = relationship("Workspace", foreign_keys="Integration.workspace_id")


class OAuthToken(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """OAuth tokens for integrations."""
    __tablename__ = "oauth_tokens"
    __table_args__ = (
        Index("ix_oauth_tokens_integration_id", "integration_id"),
        Index("ix_oauth_tokens_expires_at", "expires_at"),
    )

    integration_id: Mapped[UUID] = mapped_column(
        ForeignKey("integrations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_type: Mapped[str] = mapped_column(String(50), default="Bearer", nullable=False)
    scope: Mapped[str | None] = mapped_column(String(500), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(nullable=True, index=True)
    id_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    integration = relationship("Integration")