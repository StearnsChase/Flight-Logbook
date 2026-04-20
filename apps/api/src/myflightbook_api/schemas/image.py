from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field

from myflightbook_api.schemas.common import ORMModel


MediaTypeName = Literal["image", "pdf", "video"]


class ImageAssetRead(ORMModel):
    id: UUID
    user_id: UUID
    flight_id: UUID | None = None
    storage_key: str
    original_filename: str
    media_type: MediaTypeName
    metadata: dict[str, Any] | None = Field(default=None, alias="metadata_json")
    created_at: datetime


class ImageAssetCreate(ORMModel):
    flight_id: UUID | None = None
    storage_key: str
    original_filename: str
    media_type: MediaTypeName = "image"
    metadata: dict[str, Any] | None = None
