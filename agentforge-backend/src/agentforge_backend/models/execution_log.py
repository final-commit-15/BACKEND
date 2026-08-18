from sqlalchemy import String, Text, ForeignKey, Enum, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base import Base
from uuid import UUID
import enum

class LogSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"

class ExecutionLog(Base):
    __tablename__ = "execution_logs"
    event_type: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(Text)
    severity: Mapped[LogSeverity] = mapped_column(Enum(LogSeverity), default=LogSeverity.INFO)
    tool_used: Mapped[str] = mapped_column(String(100), nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    error_info: Mapped[dict] = mapped_column(JSON, nullable=True)
    execution_id: Mapped[UUID] = mapped_column(ForeignKey("executions.id"))

    execution = relationship("Execution", back_populates="logs")