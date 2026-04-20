from __future__ import annotations

from dataclasses import dataclass

from myflightbook_api.services.totals import summarize_flights


@dataclass
class FlightStub:
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


def test_summarize_flights_accumulates_core_totals() -> None:
    summary = summarize_flights(
        [
            FlightStub(1.2, 1.0, 0.0, 0.0, 0.2, 0.8, 0.0, 0.1, 0.0, 1, 1, 0, 1),
            FlightStub(2.3, 2.0, 0.0, 0.1, 0.0, 1.5, 0.4, 0.0, 0.3, 2, 1, 1, 2)
        ]
    )

    assert summary.flight_count == 2
    assert summary.total_flight_time == 3.5
    assert summary.pic_time == 3.0
    assert summary.cross_country == 2.3
    assert summary.landings == 3
    assert summary.approaches == 3
