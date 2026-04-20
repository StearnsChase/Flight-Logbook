from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from myflightbook_api.db.base import Base
from myflightbook_api.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


def _enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    return [item.value for item in enum_cls]


class TelemetryFormat(str, enum.Enum):
    AIRBLY = "airbly"
    BAJU = "baju"
    CSV = "csv"
    GPX = "gpx"
    IGC = "igc"
    KML = "kml"
    NMEA = "nmea"
    UNKNOWN = "unknown"


class ParseStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    PARSED = "parsed"
    PROCESSED = "processed"
    FAILED = "failed"


class MediaType(str, enum.Enum):
    IMAGE = "image"
    PDF = "pdf"
    VIDEO = "video"


class TelemetryUpload(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "telemetry_uploads"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    source_format: Mapped[TelemetryFormat] = mapped_column(
        Enum(TelemetryFormat, name="telemetry_format", values_callable=_enum_values),
        default=TelemetryFormat.UNKNOWN
    )
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(512))
    parse_status: Mapped[ParseStatus] = mapped_column(
        Enum(ParseStatus, name="parse_status", values_callable=_enum_values),
        default=ParseStatus.QUEUED
    )
    detected_departure_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    detected_arrival_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON, nullable=True)

    user: Mapped["User"] = relationship(back_populates="telemetry_uploads")
    flights: Mapped[list["Flight"]] = relationship(back_populates="telemetry_upload")


class ImageAsset(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "image_assets"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    flight_id: Mapped[str | None] = mapped_column(ForeignKey("flights.id", ondelete="SET NULL"), nullable=True)
    storage_key: Mapped[str] = mapped_column(String(512))
    original_filename: Mapped[str] = mapped_column(String(255))
    media_type: Mapped[MediaType] = mapped_column(
        Enum(MediaType, name="media_type", values_callable=_enum_values),
        default=MediaType.IMAGE
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="image_assets")
    flight: Mapped["Flight | None"] = relationship(back_populates="image_assets")


from myflightbook_api.models.flight import Flight  # noqa: E402
from myflightbook_api.models.user import User  # noqa: E402
