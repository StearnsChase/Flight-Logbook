from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

from myflightbook_api.models.aircraft import Aircraft
from myflightbook_api.models.flight import Flight
from myflightbook_api.models.user import User
from myflightbook_api.services.ratings.faa_8710 import FAA8710Service


def _flight(
    *,
    category_class: str,
    total_time: str,
    pic_time: str,
    cross_country: str = "0.0",
    night: str = "0.0",
    imc: str = "0.0",
    simulated_instrument: str = "0.0",
    landings: int = 0,
    night_landings: int = 0,
) -> Flight:
    flight = Flight(
        user_id=str(uuid4()),
        aircraft_id=str(uuid4()),
        flight_date=date(2026, 4, 20),
        route="KAPA-KBJC",
        total_time=Decimal(total_time),
        pic_time=Decimal(pic_time),
        cross_country=Decimal(cross_country),
        night=Decimal(night),
        imc=Decimal(imc),
        simulated_instrument=Decimal(simulated_instrument),
        landings=landings,
        full_stop_landings_night=night_landings,
    )
    flight.aircraft = Aircraft(
        owner_user_id=str(uuid4()),
        tail_number=f"N{uuid4().hex[:5].upper()}",
        display_name=f"{category_class} Trainer",
        category_class=category_class,
        is_complex=True,
        is_high_performance=False,
    )
    return flight


def test_calculate_totals_groups_flights_by_category_class() -> None:
    totals = FAA8710Service.calculate_totals(
        [
            _flight(category_class="ASEL", total_time="2.5", pic_time="2.5", cross_country="1.0", night="0.5", landings=2, night_landings=1),
            _flight(category_class="AMEL", total_time="1.2", pic_time="1.0", cross_country="0.8", imc="0.2", landings=1),
        ]
    )

    assert totals["Airplane Single-Engine Land"].total_time == 2.5
    assert totals["Airplane Single-Engine Land"].night_landings == 1
    assert totals["Airplane Multi-Engine Land"].actual_instrument == 0.2


def test_generate_8710_pdf_returns_pdf_bytes() -> None:
    user = User(email="pilot@example.com", display_name="Pilot Example")
    user.id = uuid4()

    pdf_bytes = FAA8710Service.generate_8710_pdf(
        {"Airplane Single-Engine Land": FAA8710Service.calculate_totals([_flight(category_class="ASEL", total_time="1.0", pic_time="1.0")])["Airplane Single-Engine Land"]},
        user,
    )

    assert pdf_bytes.startswith(b"%PDF")


def test_validate_commercial_and_instrument_requirements_report_remaining_hours() -> None:
    flights = [
        _flight(category_class="ASEL", total_time="200.0", pic_time="80.0", cross_country="40.0", imc="5.0", simulated_instrument="5.0"),
        _flight(category_class="ASEL", total_time="60.0", pic_time="25.0", cross_country="15.0", imc="10.0"),
    ]
    flights[0].distance_nm = 260.0
    flights[0].dual_received = Decimal("20.0")
    flights[1].dual_received = Decimal("5.0")

    commercial = FAA8710Service.validate_commercial_requirements(flights)
    instrument = FAA8710Service.validate_instrument_requirements(flights)

    assert commercial["eligible"] is True
    assert commercial["total_time_remaining"] == 0.0
    assert instrument["eligible"] is False
    assert instrument["instrument_time_remaining"] == 20.0
