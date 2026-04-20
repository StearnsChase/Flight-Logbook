from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field

from myflightbook_api.schemas.common import ORMModel


TelemetryFormatName = Literal["airbly", "baju", "csv", "gpx", "igc", "kml", "nmea", "unknown"]
ParseStatusName = Literal["queued", "processing", "parsed", "processed", "failed"]


class TelemetryUploadRead(ORMModel):
    id: UUID
    user_id: UUID
    source_format: TelemetryFormatName
    original_filename: str
    storage_key: str
    parse_status: ParseStatusName
    detected_departure_code: str | None = None
    detected_arrival_code: str | None = None
    metadata: dict[str, Any] | None = Field(default=None, alias="metadata_json")
    created_at: datetime
    updated_at: datetime


class TelemetryUploadCreate(ORMModel):
    source_format: TelemetryFormatName = "unknown"
    original_filename: str
    storage_key: str
    detected_departure_code: str | None = None
    detected_arrival_code: str | None = None
    metadata: dict[str, Any] | None = None
