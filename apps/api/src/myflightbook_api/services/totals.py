from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from myflightbook_api.schemas.totals import TotalsSummaryRead


def _as_float(value: Decimal | float | int) -> float:
    return float(value or 0)


def summarize_flights(flights: Iterable[object]) -> TotalsSummaryRead:
    totals = {
        "total_flight_time": 0.0,
        "pic_time": 0.0,
        "sic_time": 0.0,
        "dual_given": 0.0,
        "dual_received": 0.0,
        "cross_country": 0.0,
        "night": 0.0,
        "imc": 0.0,
        "simulated_instrument": 0.0,
        "landings": 0,
        "full_stop_landings_day": 0,
        "full_stop_landings_night": 0,
        "approaches": 0,
        "flight_count": 0
    }

    for flight in flights:
        totals["total_flight_time"] += _as_float(getattr(flight, "total_time", 0))
        totals["pic_time"] += _as_float(getattr(flight, "pic_time", 0))
        totals["sic_time"] += _as_float(getattr(flight, "sic_time", 0))
        totals["dual_given"] += _as_float(getattr(flight, "dual_given", 0))
        totals["dual_received"] += _as_float(getattr(flight, "dual_received", 0))
        totals["cross_country"] += _as_float(getattr(flight, "cross_country", 0))
        totals["night"] += _as_float(getattr(flight, "night", 0))
        totals["imc"] += _as_float(getattr(flight, "imc", 0))
        totals["simulated_instrument"] += _as_float(getattr(flight, "simulated_instrument", 0))
        totals["landings"] += int(getattr(flight, "landings", 0) or 0)
        totals["full_stop_landings_day"] += int(getattr(flight, "full_stop_landings_day", 0) or 0)
        totals["full_stop_landings_night"] += int(getattr(flight, "full_stop_landings_night", 0) or 0)
        totals["approaches"] += int(getattr(flight, "approaches", 0) or 0)
        totals["flight_count"] += 1

    return TotalsSummaryRead(**totals)
