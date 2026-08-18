from sqlalchemy import String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base import Base
from uuid import UUID
from datetime import datetime

class ApiKey(Base):
    __tablename__ = "api_keys"
    name: Mapped[str] = mapped_column(String(100))
    hashed_key: Mapped[str] = mapped_column(String(255), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))

    user = relationship("User", back_populates="api_keys")