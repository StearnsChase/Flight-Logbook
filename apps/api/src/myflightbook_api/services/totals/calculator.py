from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from myflightbook_api.models.flight import Flight
from myflightbook_api.schemas.totals import TotalsSummaryRead

ZERO_DECIMAL = Decimal("0")


@dataclass(frozen=True, slots=True)
class BasicFlightTotals:
    total_time: Decimal = ZERO_DECIMAL
    pic_time: Decimal = ZERO_DECIMAL
    sic_time: Decimal = ZERO_DECIMAL
    cross_country: Decimal = ZERO_DECIMAL
    night: Decimal = ZERO_DECIMAL
    imc: Decimal = ZERO_DECIMAL
    landings: int = 0


class FlightTotalsCalculator:
    def __init__(self, flights: Iterable[Flight]) -> None:
        self.flights = list(flights)

    def calculate_basic_totals(self) -> BasicFlightTotals:
        total_time = ZERO_DECIMAL
        pic_time = ZERO_DECIMAL
        sic_time = ZERO_DECIMAL
        cross_country = ZERO_DECIMAL
        night = ZERO_DECIMAL
        imc = ZERO_DECIMAL
        landings = 0

        for flight in self.flights:
            total_time += self._as_decimal(getattr(flight, "total_time", 0))
            pic_time += self._as_decimal(getattr(flight, "pic_time", 0))
            sic_time += self._as_decimal(getattr(flight, "sic_time", 0))
            cross_country += self._as_decimal(getattr(flight, "cross_country", 0))
            night += self._as_decimal(getattr(flight, "night", 0))
            imc += self._as_decimal(getattr(flight, "imc", 0))
            landings += self._as_int(getattr(flight, "landings", 0))

        return BasicFlightTotals(
            total_time=total_time,
            pic_time=pic_time,
            sic_time=sic_time,
            cross_country=cross_country,
            night=night,
            imc=imc,
            landings=landings,
        )

    def calculate_summary(self) -> TotalsSummaryRead:
        basic_totals = self.calculate_basic_totals()
        dual_given = ZERO_DECIMAL
        dual_received = ZERO_DECIMAL
        simulated_instrument = ZERO_DECIMAL
        full_stop_landings_day = 0
        full_stop_landings_night = 0
        approaches = 0

        for flight in self.flights:
            dual_given += self._as_decimal(getattr(flight, "dual_given", 0))
            dual_received += self._as_decimal(getattr(flight, "dual_received", 0))
            simulated_instrument += self._as_decimal(getattr(flight, "simulated_instrument", 0))
            full_stop_landings_day += self._as_int(getattr(flight, "full_stop_landings_day", 0))
            full_stop_landings_night += self._as_int(getattr(flight, "full_stop_landings_night", 0))
            approaches += self._as_int(getattr(flight, "approaches", 0))

        return TotalsSummaryRead(
            total_flight_time=float(basic_totals.total_time),
            pic_time=float(basic_totals.pic_time),
            sic_time=float(basic_totals.sic_time),
            dual_given=float(dual_given),
            dual_received=float(dual_received),
            cross_country=float(basic_totals.cross_country),
            night=float(basic_totals.night),
            imc=float(basic_totals.imc),
            simulated_instrument=float(simulated_instrument),
            landings=basic_totals.landings,
            full_stop_landings_day=full_stop_landings_day,
            full_stop_landings_night=full_stop_landings_night,
            approaches=approaches,
            flight_count=len(self.flights),
        )

    @staticmethod
    def _as_decimal(value: Decimal | float | int | None) -> Decimal:
        if value is None:
            return ZERO_DECIMAL
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))

    @staticmethod
    def _as_int(value: int | None) -> int:
        return int(value or 0)


def summarize_flights(flights: Iterable[Flight]) -> TotalsSummaryRead:
    return FlightTotalsCalculator(flights).calculate_summary()
