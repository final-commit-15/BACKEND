from sqlalchemy import String, Boolean, Enum, ForeignKey, Index, UniqueConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
import enum
from uuid import UUID
from datetime import datetime
from .base import TimestampMixin, SoftDeleteMixin, UUIDPrimaryKeyMixin


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    DEVELOPER = "developer"
    OPERATOR = "operator"
    VIEWER = "viewer"


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_email", "email"),
        Index("ix_users_username", "username"),
        Index("ix_users_active_workspace", "active_workspace_id"),
        Index("ix_users_deleted_at", "deleted_at"),
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("username", name="uq_users_username"),
    )

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    role: Mapped["UserRole"] = mapped_column(
        Enum(UserRole, values_callable=lambda x: [e.value for e in x]),
        default=UserRole.USER,
        nullable=False
    )
    active_workspace_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    oauth_accounts = relationship(
        "OAuthAccount",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    api_keys = relationship(
        "ApiKey",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    agents = relationship("Agent", back_populates="owner", foreign_keys="Agent.owner_id")
    tasks = relationship("Task", back_populates="assignee", foreign_keys="Task.assignee_id")
    notifications = relationship("Notification", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    integrations = relationship("Integration", back_populates="user")
    webhooks = relationship("Webhook", back_populates="user", foreign_keys="Webhook.user_id")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    password_resets = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    email_verifications = relationship("EmailVerificationToken", back_populates="user", cascade="all, delete-orphan")
    trusted_devices = relationship("TrustedDevice", back_populates="user", cascade="all, delete-orphan")
    login_history = relationship("LoginHistory", back_populates="user", cascade="all, delete-orphan")
    mfa_config = relationship("MFAConfig", back_populates="user", uselist=False, cascade="all, delete-orphan")


class UserSession(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """User active sessions for device tracking and revocation."""
    __tablename__ = "user_sessions"
    __table_args__ = (
        Index("ix_user_sessions_user_id", "user_id"),
        Index("ix_user_sessions_token_hash", "token_hash"),
        Index("ix_user_sessions_expires_at", "expires_at"),
        Index("ix_user_sessions_deleted_at", "deleted_at"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    device_info: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(nullable=False, index=True)
    last_activity_at: Mapped[datetime] = mapped_column(nullable=False)

    user = relationship("User", back_populates="sessions")


class RefreshToken(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Refresh token tracking for rotation and revocation."""
    __tablename__ = "refresh_tokens"
    __table_args__ = (
        Index("ix_refresh_tokens_user_id", "user_id"),
        Index("ix_refresh_tokens_token_hash", "token_hash"),
        Index("ix_refresh_tokens_expires_at", "expires_at"),
        Index("ix_refresh_tokens_revoked", "revoked"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(nullable=False, index=True)
    revoked: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(nullable=True)
    replaced_by_token_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    device_info: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    user = relationship("User", back_populates="refresh_tokens")


class PasswordResetToken(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Password reset tokens with expiry and single-use tracking."""
    __tablename__ = "password_reset_tokens"
    __table_args__ = (
        Index("ix_password_reset_tokens_user_id", "user_id"),
        Index("ix_password_reset_tokens_token_hash", "token_hash"),
        Index("ix_password_reset_tokens_expires_at", "expires_at"),
        Index("ix_password_reset_tokens_used", "used"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(nullable=False, index=True)
    used: Mapped[bool] = mapped_column(default=False, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    user = relationship("User", back_populates="password_resets")


class EmailVerificationToken(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Email verification tokens with expiry and single-use tracking."""
    __tablename__ = "email_verification_tokens"
    __table_args__ = (
        Index("ix_email_verification_tokens_user_id", "user_id"),
        Index("ix_email_verification_tokens_token_hash", "token_hash"),
        Index("ix_email_verification_tokens_expires_at", "expires_at"),
        Index("ix_email_verification_tokens_used", "used"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False, index=True)
    used: Mapped[bool] = mapped_column(default=False, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    user = relationship("User", back_populates="email_verifications")


class TrustedDevice(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Trusted devices for MFA bypass."""
    __tablename__ = "trusted_devices"
    __table_args__ = (
        Index("ix_trusted_devices_user_id", "user_id"),
        Index("ix_trusted_devices_fingerprint", "device_fingerprint"),
        Index("ix_trusted_devices_expires_at", "expires_at"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    device_fingerprint: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    device_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(nullable=False, index=True)
    last_used_at: Mapped[datetime | None] = mapped_column(nullable=True)

    user = relationship("User", back_populates="trusted_devices")


class LoginHistory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Login history for security auditing."""
    __tablename__ = "login_history"
    __table_args__ = (
        Index("ix_login_history_user_id", "user_id"),
        Index("ix_login_history_ip_address", "ip_address"),
        Index("ix_login_history_created_at", "created_at"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False, index=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    success: Mapped[bool] = mapped_column(default=True, nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mfa_used: Mapped[bool] = mapped_column(default=False, nullable=False)

    user = relationship("User", back_populates="login_history")


class MFAConfig(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """MFA configuration for users."""
    __tablename__ = "mfa_configs"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_mfa_config_user"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    secret_encrypted: Mapped[str | None] = mapped_column(String(255), nullable=True)
    backup_codes_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(nullable=True)

    user = relationship("User", back_populates="mfa_config")