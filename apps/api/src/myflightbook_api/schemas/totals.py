from __future__ import annotations

from myflightbook_api.schemas.common import ORMModel


class TotalsSummaryRead(ORMModel):
    total_flight_time: float
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
    flight_count: int
