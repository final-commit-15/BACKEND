from sqlalchemy import String, Text, JSON, ForeignKey, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from uuid import UUID
from .base import TimestampMixin, UUIDPrimaryKeyMixin
import enum


class AuditActionType(str, enum.Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXECUTE = "execute"
    ASSIGN = "assign"
    INVITE = "invite"
    EXPORT = "export"
    IMPORT = "import"


class AuditSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLog(Base, TimestampMixin, UUIDPrimaryKeyMixin):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_user_id", "user_id"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_resource_type", "resource_type"),
        Index("ix_audit_logs_resource_id", "resource_id"),
        Index("ix_audit_logs_created_at", "created_at"),
        Index("ix_audit_logs_workspace_id", "workspace_id"),
    )

    action: Mapped["AuditActionType"] = mapped_column(
        Enum(AuditActionType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
    severity: Mapped["AuditSeverity"] = mapped_column(
        Enum(AuditSeverity, values_callable=lambda x: [e.value for e in x]),
        default=AuditSeverity.INFO,
        nullable=False,
        index=True
    )
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    before_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    workspace_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user = relationship("User", back_populates="audit_logs", foreign_keys="AuditLog.user_id")
    workspace = relationship("Workspace", foreign_keys=[workspace_id])