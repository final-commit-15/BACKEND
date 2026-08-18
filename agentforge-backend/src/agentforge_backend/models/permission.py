from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from ..db.base import Base

class Permission(Base):
    __tablename__ = "permissions"
    name: Mapped[str] = mapped_column(String(100), unique=True)
    resource: Mapped[str] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(50))