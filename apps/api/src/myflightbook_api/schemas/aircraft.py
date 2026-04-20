from __future__ import annotations

from datetime import datetime
from uuid import UUID

from myflightbook_api.schemas.common import ORMModel


class AircraftRead(ORMModel):
    id: UUID
    tail_number: str
    display_name: str
    model_name: str | None = None
    category_class: str | None = None
    engine_type: str | None = None
    is_complex: bool
    is_high_performance: bool
    is_retractable: bool
    created_at: datetime
    updated_at: datetime


class AircraftCreate(ORMModel):
    tail_number: str
    display_name: str
    model_name: str | None = None
    category_class: str | None = None
    engine_type: str | None = None
    is_complex: bool = False
    is_high_performance: bool = False
    is_retractable: bool = False


class AircraftUpdate(ORMModel):
    display_name: str | None = None
    model_name: str | None = None
    category_class: str | None = None
    engine_type: str | None = None
    is_complex: bool | None = None
    is_high_performance: bool | None = None
    is_retractable: bool | None = None
