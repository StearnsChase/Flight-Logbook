from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from myflightbook_api.schemas.common import ORMModel


class FlightRead(ORMModel):
    id: UUID
    aircraft_id: UUID
    flight_date: date
    route: str
    total_time: float
    pic_time: float
    sic_time: float
    dual_given: float
    dual_received: float
    cross_country: float
    night: float
    imc: float
    simulated_instrument: float
    landings: int
    full_stop_landings_day: int
    full_stop_landings_night: int
    approaches: int
    remarks: str | None = None
    created_at: datetime
    updated_at: datetime


class FlightCreate(ORMModel):
    aircraft_id: UUID
    telemetry_upload_id: UUID | None = None
    flight_date: date
    route: str = ""
    remarks: str | None = None
    total_time: float = 0
    pic_time: float = 0
    sic_time: float = 0
    dual_given: float = 0
    dual_received: float = 0
    cross_country: float = 0
    night: float = 0
    imc: float = 0
    simulated_instrument: float = 0
    landings: int = 0
    full_stop_landings_day: int = 0
    full_stop_landings_night: int = 0
    approaches: int = 0


class FlightUpdate(ORMModel):
    route: str | None = None
    remarks: str | None = None
    total_time: float | None = None
    pic_time: float | None = None
    sic_time: float | None = None
    dual_given: float | None = None
    dual_received: float | None = None
    cross_country: float | None = None
    night: float | None = None
    imc: float | None = None
    simulated_instrument: float | None = None
    landings: int | None = None
    full_stop_landings_day: int | None = None
    full_stop_landings_night: int | None = None
    approaches: int | None = None
