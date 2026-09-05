from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, func
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional


class Base(DeclarativeBase):
    """Base class for all models with common columns."""
    pass


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class SoftDeleteMixin:
    """Mixin for soft delete support."""
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        index=True
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class UUIDPrimaryKeyMixin:
    """Mixin for UUID primary key."""
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        nullable=False
    )