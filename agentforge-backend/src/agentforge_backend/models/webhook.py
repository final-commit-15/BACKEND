from sqlalchemy import String, Text, ForeignKey, JSON, Boolean, Index, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from uuid import UUID
from datetime import datetime
from .base import TimestampMixin, SoftDeleteMixin, UUIDPrimaryKeyMixin
import enum


class WebhookStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DISABLED = "disabled"


class Webhook(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "webhooks"
    __table_args__ = (
        Index("ix_webhooks_user_id", "user_id"),
        Index("ix_webhooks_project_id", "project_id"),
        Index("ix_webhooks_status", "status"),
        Index("ix_webhooks_deleted_at", "deleted_at"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    secret: Mapped[str] = mapped_column(String(255), nullable=False)
    events: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(WebhookStatus, values_callable=lambda x: [e.value for e in x]),
        default=WebhookStatus.ACTIVE,
        nullable=False,
        index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    retry_config: Mapped[dict] = mapped_column(JSON, default={"max_retries": 3, "backoff_seconds": 60}, nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    headers: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    last_triggered_at: Mapped[datetime | None] = mapped_column(nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(nullable=True)
    failure_count: Mapped[int] = mapped_column(default=0, nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    project = relationship("Project", foreign_keys="Webhook.project_id")
    deliveries = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")


class WebhookDelivery(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Webhook delivery tracking for debugging and retry logic."""
    __tablename__ = "webhook_deliveries"
    __table_args__ = (
        Index("ix_webhook_deliveries_webhook_id", "webhook_id"),
        Index("ix_webhook_deliveries_status", "status"),
        Index("ix_webhook_deliveries_created_at", "created_at"),
    )

    webhook_id: Mapped[UUID] = mapped_column(
        ForeignKey("webhooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    response_status: Mapped[int | None] = mapped_column(nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_headers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    attempt: Mapped[int] = mapped_column(default=1, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(nullable=True)

    webhook = relationship("Webhook", back_populates="deliveries")