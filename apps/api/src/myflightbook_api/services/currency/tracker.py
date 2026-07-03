from __future__ import annotations

import calendar
import enum
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
import math
from typing import Sequence

from myflightbook_api.models.deadline import Deadline
from myflightbook_api.models.flight import Flight


class CurrencyState(enum.IntEnum):
    UNKNOWN = -1
    OK = 0
    NOT_CURRENT = 1
    GETTING_CLOSE = 2
    NO_DATE = 3


@dataclass
class CurrencyStatusItem:
    label: str
    status_text: str
    state: CurrencyState
    discrepancy: str = ""
    currency_group: str = ""


ZERO_DECIMAL = Decimal("0")


def _current_time() -> datetime:
    return datetime.now()


def _as_decimal(value: Decimal | float | int | None) -> Decimal:
    if value is None:
        return ZERO_DECIMAL
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _as_int(value: int | float | None) -> int:
    return int(value or 0)


def _add_calendar_months(dt: datetime, months: int) -> datetime:
    target_month = dt.month - 1 + months
    year = dt.year + target_month // 12
    month = target_month % 12 + 1
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


def _flight_date_as_datetime(flight: Flight) -> datetime | None:
    flight_date = getattr(flight, "flight_date", None)
    if isinstance(flight_date, datetime):
        return flight_date
    if isinstance(flight_date, date):
        return datetime.combine(flight_date, time.min)
    return None


def _hours_progress(deadline: Deadline) -> tuple[str, Decimal] | None:
    candidates: list[tuple[str, Decimal]] = []
    for label, attr in (("hobbs", "high_water_hobbs"), ("tach", "high_water_tach")):
        value = getattr(deadline, attr, getattr(deadline, attr.title().replace("_", ""), None))
        decimal_value = _as_decimal(value)
        if decimal_value > 0:
            candidates.append((label, decimal_value))

    if not candidates:
        return None

    target = _as_decimal(deadline.aircraft_hours)
    return min(candidates, key=lambda item: abs(item[1] - target))


def _format_hours_status(target: Decimal, source_label: str, current_value: Decimal) -> tuple[CurrencyState, str]:
    delta = current_value - target
    remaining = abs(delta)
    if delta < Decimal("-10"):
        state = CurrencyState.OK
    elif delta < 0:
        state = CurrencyState.GETTING_CLOSE
    else:
        state = CurrencyState.NOT_CURRENT

    if delta < 0:
        discrepancy = f"{source_label.title()} {float(current_value):.1f}; {float(remaining):.1f} hours remaining"
    elif delta > 0:
        discrepancy = f"{source_label.title()} {float(current_value):.1f}; overdue by {float(remaining):.1f} hours"
    else:
        discrepancy = f"{source_label.title()} {float(current_value):.1f}; due now"

    return state, discrepancy


def _hold_or_intercept_count(flight: Flight) -> int:
    for attr in ("holding_procedures", "holds", "hold_count", "holding", "intercepts", "intercepting_tasks"):
        value = getattr(flight, attr, None)
        if isinstance(value, bool):
            return 1 if value else 0
        if value:
            return max(1, _as_int(value))

    remarks = (getattr(flight, "remarks", "") or "").lower()
    return 1 if ("hold" in remarks or "intercept" in remarks) else 0


class CurrencyTrackerService:
    @staticmethod
    def calculate_new_due_date(deadline: Deadline, renewed_date: datetime) -> datetime:
        match deadline.regen_type:
            case deadline.regen_type.NONE:
                return renewed_date
            case deadline.regen_type.DAYS:
                return renewed_date + timedelta(days=deadline.regen_span)
            case deadline.regen_type.CALENDAR_MONTHS:
                return _add_calendar_months(renewed_date, deadline.regen_span)
            case deadline.regen_type.HOURS:
                raise ValueError("Deadline is hour based, not date based")
            case _:
                return renewed_date

    @staticmethod
    def get_currency_status_for_deadlines(deadlines: Sequence[Deadline], days_for_warning: int = 30) -> list[CurrencyStatusItem]:
        now = _current_time()
        items: list[CurrencyStatusItem] = []

        for deadline in deadlines:
            label = deadline.name
            currency_group = "aircraft_deadline" if deadline.is_shared_aircraft_deadline else "deadline"

            if deadline.uses_hours:
                progress = _hours_progress(deadline)
                if progress is None:
                    items.append(
                        CurrencyStatusItem(
                            label=label,
                            status_text="No hour tracking data",
                            state=CurrencyState.NO_DATE,
                            currency_group=currency_group,
                        )
                    )
                    continue

                source_label, current_value = progress
                target = _as_decimal(deadline.aircraft_hours)
                state, discrepancy = _format_hours_status(target, source_label, current_value)
                items.append(
                    CurrencyStatusItem(
                        label=label,
                        status_text=f"{float(target):,.1f}",
                        state=state,
                        discrepancy=discrepancy,
                        currency_group=currency_group,
                    )
                )
                continue

            if deadline.expiration is None:
                items.append(
                    CurrencyStatusItem(
                        label=label,
                        status_text="No due date",
                        state=CurrencyState.NO_DATE,
                        currency_group=currency_group,
                    )
                )
                continue

            delta = deadline.expiration - now
            days_until_due = math.ceil(delta.total_seconds() / 86400)
            if delta.total_seconds() < 0:
                state = CurrencyState.NOT_CURRENT
                discrepancy = f"Overdue by {abs(days_until_due)} day(s)"
            elif days_until_due < days_for_warning:
                state = CurrencyState.GETTING_CLOSE
                discrepancy = f"{days_until_due} day(s) remaining"
            else:
                state = CurrencyState.OK
                discrepancy = ""

            items.append(
                CurrencyStatusItem(
                    label=label,
                    status_text=deadline.expiration.date().isoformat(),
                    state=state,
                    discrepancy=discrepancy,
                    currency_group=currency_group,
                )
            )

        return items

    @staticmethod
    def compute_night_currency(flights: Sequence[Flight]) -> CurrencyStatusItem:
        cutoff = _current_time().date() - timedelta(days=90)
        qualifying_landings = sum(
            _as_int(getattr(flight, "full_stop_landings_night", 0))
            for flight in flights
            if getattr(flight, "flight_date", None) and getattr(flight, "flight_date") >= cutoff
        )

        if qualifying_landings >= 3:
            state = CurrencyState.OK
            discrepancy = ""
        elif qualifying_landings > 0:
            state = CurrencyState.GETTING_CLOSE
            discrepancy = f"Need {3 - qualifying_landings} more full-stop night landing(s)"
        else:
            state = CurrencyState.NOT_CURRENT
            discrepancy = "Need 3 full-stop night landings"

        return CurrencyStatusItem(
            label="Night Currency",
            status_text=f"{qualifying_landings}/3 full-stop night landings",
            state=state,
            discrepancy=discrepancy,
            currency_group="currency",
        )

    @staticmethod
    def compute_ifr_currency(flights: Sequence[Flight]) -> CurrencyStatusItem:
        cutoff = _add_calendar_months(_current_time(), -6)
        approaches = 0
        holds = 0

        for flight in flights:
            flight_dt = _flight_date_as_datetime(flight)
            if flight_dt is None or flight_dt < cutoff:
                continue

            approaches += _as_int(getattr(flight, "approaches", 0))
            holds += _hold_or_intercept_count(flight)

        is_current = approaches >= 6 and holds > 0
        if is_current:
            state = CurrencyState.OK
            discrepancy = ""
        elif approaches > 0 or holds > 0:
            state = CurrencyState.GETTING_CLOSE
            missing: list[str] = []
            if approaches < 6:
                missing.append(f"{6 - approaches} approach(es)")
            if holds == 0:
                missing.append("holding/intercepting")
            discrepancy = "Need " + " and ".join(missing)
        else:
            state = CurrencyState.NOT_CURRENT
            discrepancy = "Need 6 approaches and holding/intercepting"

        return CurrencyStatusItem(
            label="IFR Currency",
            status_text=f"{approaches}/6 approaches, holding/intercepting: {'yes' if holds > 0 else 'no'}",
            state=state,
            discrepancy=discrepancy,
            currency_group="currency",
        )
