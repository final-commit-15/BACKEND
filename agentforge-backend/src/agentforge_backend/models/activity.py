from sqlalchemy import String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID, uuid4
from datetime import datetime
from .base import Base

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(String(50))
    action: Mapped[str] = mapped_column(String(255))
    extra_data: Mapped[dict] = mapped_column(JSON, nullable=True)   # <<-- renamed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)