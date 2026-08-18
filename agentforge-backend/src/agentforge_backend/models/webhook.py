from sqlalchemy import String, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base import Base
from uuid import UUID

class Webhook(Base):
    __tablename__ = "webhooks"
    name: Mapped[str] = mapped_column(String(100))
    url: Mapped[str] = mapped_column(String(500))
    secret: Mapped[str] = mapped_column(String(255))
    events: Mapped[list] = mapped_column(JSON, default=list)  # list of event types
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    retry_config: Mapped[dict] = mapped_column(JSON, default={"max_retries": 3, "backoff_seconds": 60})
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), nullable=True)

    user = relationship("User")
    project = relationship("Project")