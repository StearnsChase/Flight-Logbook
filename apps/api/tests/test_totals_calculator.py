from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

from myflightbook_api.models.flight import Flight
from myflightbook_api.services.totals import FlightTotalsCalculator


def _flight(
    *,
    total_time: Decimal | str = "0.00",
    pic_time: Decimal | str = "0.00",
    sic_time: Decimal | str = "0.00",
    cross_country: Decimal | str = "0.00",
    night: Decimal | str = "0.00",
    imc: Decimal | str = "0.00",
    landings: int = 0,
) -> Flight:
    return Flight(
        user_id=str(uuid4()),
        aircraft_id=str(uuid4()),
        flight_date=date(2026, 4, 20),
        route="KAPA-KBJC",
        total_time=Decimal(total_time),
        pic_time=Decimal(pic_time),
        sic_time=Decimal(sic_time),
        cross_country=Decimal(cross_country),
        night=Decimal(night),
        imc=Decimal(imc),
        landings=landings,
    )


def test_calculate_basic_totals_returns_zeroed_totals_for_empty_logbook() -> None:
    totals = FlightTotalsCalculator([]).calculate_basic_totals()

    assert totals.total_time == Decimal("0")
    assert totals.pic_time == Decimal("0")
    assert totals.sic_time == Decimal("0")
    assert totals.cross_country == Decimal("0")
    assert totals.night == Decimal("0")
    assert totals.imc == Decimal("0")
    assert totals.landings == 0


def test_calculate_basic_totals_accumulates_all_requested_fields() -> None:
    calculator = FlightTotalsCalculator(
        [
            _flight(
                total_time="1.20",
                pic_time="1.00",
                sic_time="0.20",
                cross_country="0.90",
                night="0.10",
                imc="0.00",
                landings=1,
            ),
            _flight(
                total_time="2.35",
                pic_time="1.50",
                sic_time="0.85",
                cross_country="1.75",
                night="0.40",
                imc="0.25",
                landings=2,
            ),
        ]
    )

    totals = calculator.calculate_basic_totals()

    assert totals.total_time == Decimal("3.55")
    assert totals.pic_time == Decimal("2.50")
    assert totals.sic_time == Decimal("1.05")
    assert totals.cross_country == Decimal("2.65")
    assert totals.night == Decimal("0.50")
    assert totals.imc == Decimal("0.25")
    assert totals.landings == 3


def test_calculate_basic_totals_avoids_float_rounding_artifacts() -> None:
    calculator = FlightTotalsCalculator(
        [
            _flight(total_time="0.10", pic_time="0.10", sic_time="0.00", cross_country="0.10", night="0.00", imc="0.00"),
            _flight(total_time="0.20", pic_time="0.20", sic_time="0.00", cross_country="0.20", night="0.00", imc="0.00"),
            _flight(total_time="0.30", pic_time="0.30", sic_time="0.00", cross_country="0.30", night="0.00", imc="0.00"),
        ]
    )

    totals = calculator.calculate_basic_totals()

    assert totals.total_time == Decimal("0.60")
    assert totals.pic_time == Decimal("0.60")
    assert totals.cross_country == Decimal("0.60")


def test_calculate_basic_totals_accepts_float_backed_values_without_precision_loss() -> None:
    flights = [
        _flight(),
        _flight(),
    ]
    flights[0].total_time = 0.1
    flights[0].pic_time = 0.1
    flights[0].sic_time = 0.0
    flights[0].cross_country = 0.1
    flights[0].night = 0.0
    flights[0].imc = 0.0
    flights[0].landings = 1
    flights[1].total_time = 0.2
    flights[1].pic_time = 0.2
    flights[1].sic_time = 0.0
    flights[1].cross_country = 0.2
    flights[1].night = 0.0
    flights[1].imc = 0.0
    flights[1].landings = 2

    totals = FlightTotalsCalculator(flights).calculate_basic_totals()

    assert totals.total_time == Decimal("0.3")
    assert totals.pic_time == Decimal("0.3")
    assert totals.cross_country == Decimal("0.3")
    assert totals.landings == 3
