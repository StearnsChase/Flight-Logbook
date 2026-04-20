from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from myflightbook_api.db.base import Base
from myflightbook_api.models.mixins import UUIDPrimaryKeyMixin


class LegacyEntityMapping(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "legacy_entity_mappings"
    __table_args__ = (
        UniqueConstraint("legacy_system", "legacy_table", "legacy_identifier", name="uq_legacy_mapping_source"),
    )

    legacy_system: Mapped[str] = mapped_column(String(64))
    legacy_table: Mapped[str] = mapped_column(String(128))
    legacy_identifier: Mapped[str] = mapped_column(String(255))
    entity_type: Mapped[str] = mapped_column(String(64), index=True)
    canonical_entity_id: Mapped[str] = mapped_column(String(36), index=True)
    mapping_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
