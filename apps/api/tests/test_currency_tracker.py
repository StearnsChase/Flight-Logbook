from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from myflightbook_api.models.deadline import Deadline, RegenUnit
from myflightbook_api.models.flight import Flight
from myflightbook_api.services.currency import tracker as tracker_service
from myflightbook_api.services.currency.tracker import CurrencyState, CurrencyTrackerService


def _deadline(*, name: str, regen_type: RegenUnit, regen_span: int = 0, expiration: datetime | None = None) -> Deadline:
    deadline = Deadline(name=name, regen_type=regen_type, regen_span=regen_span)
    deadline.expiration = expiration
    return deadline


def _flight(*, flight_date: date, approaches: int = 0, night_landings: int = 0, remarks: str | None = None) -> Flight:
    return Flight(
        user_id=str(uuid4()),
        aircraft_id=str(uuid4()),
        flight_date=flight_date,
        route="KAPA-KBJC",
        total_time=Decimal("1.5"),
        pic_time=Decimal("1.5"),
        night=Decimal("0.5") if night_landings else Decimal("0"),
        full_stop_landings_night=night_landings,
        approaches=approaches,
        remarks=remarks,
    )


def test_calculate_new_due_date_supports_days_and_calendar_months() -> None:
    renewed = datetime(2026, 1, 31, 9, 15, 0)
    day_deadline = _deadline(name="Flight Review", regen_type=RegenUnit.DAYS, regen_span=90)
    month_deadline = _deadline(name="Medical", regen_type=RegenUnit.CALENDAR_MONTHS, regen_span=12)

    assert CurrencyTrackerService.calculate_new_due_date(day_deadline, renewed) == datetime(2026, 5, 1, 9, 15, 0)
    assert CurrencyTrackerService.calculate_new_due_date(month_deadline, renewed) == datetime(2027, 1, 31, 9, 15, 0)


def test_calculate_new_due_date_rejects_hour_based_deadlines() -> None:
    deadline = _deadline(name="Oil Change", regen_type=RegenUnit.HOURS, regen_span=50)

    with pytest.raises(ValueError, match="hour based"):
        CurrencyTrackerService.calculate_new_due_date(deadline, datetime(2026, 4, 20, 0, 0, 0))


def test_get_currency_status_for_deadlines_handles_calendar_and_hour_deadlines(monkeypatch: pytest.MonkeyPatch) -> None:
    now = datetime(2026, 4, 20, 12, 0, 0)
    monkeypatch.setattr(tracker_service, "_current_time", lambda: now)

    close_deadline = _deadline(
        name="Flight Review",
        regen_type=RegenUnit.DAYS,
        regen_span=90,
        expiration=now + timedelta(days=10),
    )
    overdue_deadline = _deadline(
        name="Medical",
        regen_type=RegenUnit.CALENDAR_MONTHS,
        regen_span=12,
        expiration=now - timedelta(days=3),
    )
    hours_deadline = _deadline(name="Oil Change", regen_type=RegenUnit.HOURS, regen_span=50)
    hours_deadline.aircraft_id = str(uuid4())
    hours_deadline.aircraft_hours = Decimal("120.0")
    hours_deadline.high_water_hobbs = Decimal("115.5")

    statuses = CurrencyTrackerService.get_currency_status_for_deadlines(
        [close_deadline, overdue_deadline, hours_deadline],
        days_for_warning=30,
    )

    assert statuses[0].state == CurrencyState.GETTING_CLOSE
    assert statuses[1].state == CurrencyState.NOT_CURRENT
    assert statuses[2].state == CurrencyState.GETTING_CLOSE
    assert "hours remaining" in statuses[2].discrepancy


def test_compute_night_currency_counts_recent_full_stop_night_landings(monkeypatch: pytest.MonkeyPatch) -> None:
    now = datetime(2026, 4, 20, 12, 0, 0)
    monkeypatch.setattr(tracker_service, "_current_time", lambda: now)

    flights = [
        _flight(flight_date=date(2026, 4, 10), night_landings=2),
        _flight(flight_date=date(2026, 3, 15), night_landings=1),
        _flight(flight_date=date(2025, 12, 1), night_landings=4),
    ]

    status = CurrencyTrackerService.compute_night_currency(flights)

    assert status.state == CurrencyState.OK
    assert status.status_text == "3/3 full-stop night landings"


def test_compute_ifr_currency_requires_six_approaches_and_a_hold(monkeypatch: pytest.MonkeyPatch) -> None:
    now = datetime(2026, 4, 20, 12, 0, 0)
    monkeypatch.setattr(tracker_service, "_current_time", lambda: now)

    flights = [
        _flight(flight_date=date(2026, 4, 19), approaches=4, remarks="ILS practice and hold at BJC"),
        _flight(flight_date=date(2026, 2, 5), approaches=2, remarks="RNAV approach"),
    ]

    status = CurrencyTrackerService.compute_ifr_currency(flights)

    assert status.state == CurrencyState.OK
    assert status.status_text.startswith("6/6 approaches")
