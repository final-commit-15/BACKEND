from sqlalchemy import String, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base import Base
from uuid import UUID

class AuditLog(Base):
    __tablename__ = "audit_logs"
    action: Mapped[str] = mapped_column(String(50))
    resource_type: Mapped[str] = mapped_column(String(50))
    resource_id: Mapped[str] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, nullable=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=True)

    user = relationship("User", back_populates="audit_logs")