from sqlalchemy import String, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base import Base
from uuid import UUID

class Integration(Base):
    __tablename__ = "integrations"
    name: Mapped[str] = mapped_column(String(100))
    provider: Mapped[str] = mapped_column(String(50))
    encrypted_credentials: Mapped[str] = mapped_column(Text)  # store encrypted JSON
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))

    user = relationship("User", back_populates="integrations")