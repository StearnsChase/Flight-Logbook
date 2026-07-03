from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence

from myflightbook_api.models.category_class import CatClassID
from myflightbook_api.models.flight import Flight
from myflightbook_api.models.user import User
from myflightbook_api.services.printing.pdf_generator import build_basic_pdf

@dataclass
class FAA8710Totals:
    total_time: float = 0.0
    instruction_received: float = 0.0
    solo_time: float = 0.0
    pic_time: float = 0.0
    sic_time: float = 0.0
    cross_country: float = 0.0
    day_time: float = 0.0
    night_time: float = 0.0
    actual_instrument: float = 0.0
    simulated_instrument: float = 0.0
    simulator: float = 0.0
    night_takeoffs: int = 0
    night_landings: int = 0
    total_landings: int = 0
    
class FAA8710Service:
    """
    Generates totals required for an FAA 8710 / IACRA application.
    """

    @staticmethod
    def calculate_totals(flights: Sequence[Flight]) -> dict[str, FAA8710Totals]:
        grouped_totals: dict[str, FAA8710Totals] = {}

        for flight in flights:
            category = _resolve_category_class_id(flight)
            if category is None:
                continue

            label = _category_label(category)
            bucket = grouped_totals.setdefault(label, FAA8710Totals())
            total_time = _as_float(getattr(flight, "total_time", 0.0))
            night_time = _as_float(getattr(flight, "night", 0.0))
            actual_instrument = _as_float(getattr(flight, "imc", 0.0))
            simulated_instrument = _as_float(getattr(flight, "simulated_instrument", 0.0))

            bucket.total_time += total_time
            bucket.instruction_received += _as_float(getattr(flight, "dual_received", 0.0))
            bucket.solo_time += _as_float(getattr(flight, "solo_time", getattr(flight, "solo", 0.0)))
            bucket.pic_time += _as_float(getattr(flight, "pic_time", 0.0))
            bucket.sic_time += _as_float(getattr(flight, "sic_time", 0.0))
            bucket.cross_country += _as_float(getattr(flight, "cross_country", 0.0))
            bucket.day_time += max(total_time - night_time, 0.0)
            bucket.night_time += night_time
            bucket.actual_instrument += actual_instrument
            bucket.simulated_instrument += simulated_instrument
            bucket.simulator += total_time if _is_simulator(flight) else 0.0
            bucket.night_takeoffs += _as_int(getattr(flight, "night_takeoffs", 0))
            bucket.night_landings += _as_int(getattr(flight, "full_stop_landings_night", 0))
            bucket.total_landings += _as_int(getattr(flight, "landings", 0))

        return grouped_totals

    @staticmethod
    def generate_8710_pdf(totals: dict[str, FAA8710Totals], user: User) -> bytes:
        lines = [
            "FAA 8710 / IACRA Totals",
            f"Applicant: {getattr(user, 'display_name', 'Unknown Applicant')}",
            "",
        ]
        for category_name, bucket in totals.items():
            lines.append(category_name)
            lines.append(
                "  "
                f"Total {bucket.total_time:.1f} | PIC {bucket.pic_time:.1f} | SIC {bucket.sic_time:.1f} | "
                f"XC {bucket.cross_country:.1f} | Night {bucket.night_time:.1f} | "
                f"Actual {bucket.actual_instrument:.1f} | Sim {bucket.simulated_instrument:.1f}"
            )

        return build_basic_pdf("\n".join(lines))

    @staticmethod
    def validate_commercial_requirements(flights: Sequence[Flight]) -> dict[str, bool | float]:
        total_time = sum(_as_float(getattr(flight, "total_time", 0.0)) for flight in flights)
        pic_time = sum(_as_float(getattr(flight, "pic_time", 0.0)) for flight in flights)
        cross_country = sum(_as_float(getattr(flight, "cross_country", 0.0)) for flight in flights)
        instrument_time = sum(
            _as_float(getattr(flight, "imc", 0.0)) + _as_float(getattr(flight, "simulated_instrument", 0.0))
            for flight in flights
        )
        complex_or_taa = sum(_as_float(getattr(flight, "total_time", 0.0)) for flight in flights if _is_complex_or_taa(flight))

        requirements = {
            "total_time_remaining": max(250.0 - total_time, 0.0),
            "pic_time_remaining": max(100.0 - pic_time, 0.0),
            "cross_country_remaining": max(50.0 - cross_country, 0.0),
            "instrument_time_remaining": max(10.0 - instrument_time, 0.0),
            "complex_or_taa_remaining": max(10.0 - complex_or_taa, 0.0),
        }
        eligible = all(value == 0.0 for value in requirements.values())

        return {
            "eligible": eligible,
            "total_time": total_time,
            "pic_time": pic_time,
            "cross_country": cross_country,
            "instrument_time": instrument_time,
            "complex_or_taa_time": complex_or_taa,
            **requirements,
        }

    @staticmethod
    def validate_instrument_requirements(flights: Sequence[Flight]) -> dict[str, bool | float]:
        pic_cross_country = sum(
            _as_float(getattr(flight, "cross_country", 0.0))
            for flight in flights
            if _as_float(getattr(flight, "pic_time", 0.0)) > 0
        )
        instrument_time = sum(
            _as_float(getattr(flight, "imc", 0.0)) + _as_float(getattr(flight, "simulated_instrument", 0.0))
            for flight in flights
        )
        cfii_time = sum(
            _as_float(getattr(flight, "cfii_time", getattr(flight, "dual_received", 0.0)))
            for flight in flights
            if _as_float(getattr(flight, "imc", 0.0)) + _as_float(getattr(flight, "simulated_instrument", 0.0)) > 0
        )
        long_cross_country_met = any(_has_qualifying_long_xc(flight) for flight in flights)

        requirements = {
            "pic_cross_country_remaining": max(50.0 - pic_cross_country, 0.0),
            "instrument_time_remaining": max(40.0 - instrument_time, 0.0),
            "cfii_time_remaining": max(15.0 - cfii_time, 0.0),
        }
        eligible = all(value == 0.0 for value in requirements.values()) and long_cross_country_met

        return {
            "eligible": eligible,
            "pic_cross_country": pic_cross_country,
            "instrument_time": instrument_time,
            "cfii_time": cfii_time,
            "long_cross_country_met": long_cross_country_met,
            **requirements,
        }


def _as_float(value: Decimal | float | int | None) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _as_int(value: int | float | None) -> int:
    return int(value or 0)


def _resolve_category_class_id(flight: Flight) -> CatClassID | None:
    candidates = [
        getattr(flight, "category_class_id", None),
        getattr(flight, "cat_class_id", None),
        getattr(getattr(flight, "aircraft", None), "category_class", None),
        getattr(flight, "category_class", None),
    ]

    for candidate in candidates:
        if candidate is None:
            continue
        if isinstance(candidate, CatClassID):
            return candidate
        if isinstance(candidate, str):
            normalized = candidate.strip().upper()
            if normalized in CatClassID.__members__:
                return CatClassID[normalized]
        try:
            return CatClassID(int(candidate))
        except (TypeError, ValueError):
            continue

    return None


def _category_label(category: CatClassID) -> str:
    mapping = {
        CatClassID.ASEL: "Airplane Single-Engine Land",
        CatClassID.AMEL: "Airplane Multi-Engine Land",
        CatClassID.ASES: "Airplane Single-Engine Sea",
        CatClassID.AMES: "Airplane Multi-Engine Sea",
        CatClassID.HELICOPTER: "Helicopter",
        CatClassID.GLIDER: "Glider",
    }
    if category in mapping:
        return mapping[category]
    if category.is_lighter_than_air:
        return "Lighter-Than-Air"
    return category.name.replace("_", " ").title()


def _is_simulator(flight: Flight) -> bool:
    for candidate in (
        getattr(flight, "is_simulator", None),
        getattr(getattr(flight, "aircraft", None), "is_simulator", None),
        getattr(getattr(flight, "make_model", None), "allowed_types", None),
    ):
        if isinstance(candidate, bool):
            return candidate
        if candidate is not None and str(candidate).upper().endswith("SIMULATOR_ONLY"):
            return True

    return False


def _is_complex_or_taa(flight: Flight) -> bool:
    aircraft = getattr(flight, "aircraft", None)
    make_model = getattr(flight, "make_model", None)
    return bool(
        getattr(aircraft, "is_complex", False)
        or getattr(aircraft, "is_high_performance", False)
        or getattr(make_model, "is_all_taa", False)
        or getattr(flight, "is_taa", False)
    )


def _has_qualifying_long_xc(flight: Flight) -> bool:
    distance_nm = _as_float(
        getattr(
            flight,
            "cross_country_distance_nm",
            getattr(flight, "distance_nm", getattr(flight, "route_distance_nm", 0.0)),
        )
    )
    return (
        _as_float(getattr(flight, "cross_country", 0.0)) > 0
        and _as_float(getattr(flight, "pic_time", 0.0)) > 0
        and distance_nm >= 250.0
    )
