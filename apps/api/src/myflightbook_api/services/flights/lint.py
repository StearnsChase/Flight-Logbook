from __future__ import annotations

import asyncio
import enum
from dataclasses import dataclass
from typing import Sequence

from myflightbook_api.models.flight import Flight
from myflightbook_api.models.make_model import MakeModel
from myflightbook_api.models.aircraft import Aircraft
from myflightbook_api.models.category_class import CatClassID
from myflightbook_api.services.geography.airports import AirportQueryService, RouteParser
from myflightbook_api.services.geography.latlong import LatLong


class LintOptions(enum.IntFlag):
    NONE = 0x0000
    SIM_ISSUES = 0x0001
    IFR_ISSUES = 0x0002
    AIRPORT_ISSUES = 0x0004
    XC_ISSUES = 0x0008
    PIC_SIC_DUAL_MATH = 0x0010
    TIME_ISSUES = 0x0020
    DATE_TIME_ISSUES = 0x0040
    MISC_ISSUES = 0x8000
    INCLUDE_IGNORED = 0x00010000

    @classmethod
    def default_options(cls, is_us_locale: bool = True) -> int:
        options = ~cls.INCLUDE_IGNORED
        if is_us_locale:
            options &= ~cls.PIC_SIC_DUAL_MATH
        return options


@dataclass
class FlightIssue:
    area: LintOptions
    issue_description: str


@dataclass
class FlightWithIssues:
    flight: Flight
    issues: list[FlightIssue]


class FlightLint:
    """
    Service to validate flights against common logical errors (e.g., PIC time > Total time, 
    Cross country distance mismatch, logging water landings in a land plane).
    """

    IGNORE_MARKER = "\u2006"

    def __init__(self):
        self.current_issues: list[FlightIssue] = []

    def check_flights(self, flights: Sequence[Flight], options: int) -> list[FlightWithIssues]:
        if not flights or options == 0:
            return []

        flights_with_issues: list[FlightWithIssues] = []

        for flight in flights:
            self.current_issues = []
            if not (options & LintOptions.INCLUDE_IGNORED) and (getattr(flight, "route", "") or "").endswith(self.IGNORE_MARKER):
                continue

            aircraft = getattr(flight, "aircraft", None)
            model = getattr(flight, "make_model", None) or getattr(aircraft, "make_model", None)

            if aircraft is None:
                self.current_issues.append(
                    FlightIssue(area=LintOptions.MISC_ISSUES, issue_description="Aircraft is not loaded for this flight")
                )
                flights_with_issues.append(FlightWithIssues(flight=flight, issues=list(self.current_issues)))
                continue

            if options & LintOptions.SIM_ISSUES:
                self._check_sim_issues(flight, aircraft, model)
            if options & LintOptions.IFR_ISSUES:
                self._check_ifr_issues(flight, aircraft, model)
            if options & LintOptions.TIME_ISSUES:
                self._check_time_issues(flight, aircraft, model)
            if options & LintOptions.AIRPORT_ISSUES:
                self._check_airport_issues_sync(flight, aircraft, model)
            if options & LintOptions.MISC_ISSUES:
                self._check_misc_issues(flight, aircraft, model)

            if self.current_issues:
                flights_with_issues.append(FlightWithIssues(flight=flight, issues=list(self.current_issues)))

        return flights_with_issues

    def _check_sim_issues(self, flight: Flight, aircraft: Aircraft, model: MakeModel) -> None:
        is_simulator = self._is_simulator(aircraft, model)
        sim_registration = bool(getattr(flight, "sim_registration", None) or getattr(aircraft, "sim_registration", None))
        ground_sim = self._as_float(getattr(flight, "ground_sim", 0.0))

        if is_simulator:
            self._add_conditional_issue(self._as_float(flight.pic_time) > 0, LintOptions.SIM_ISSUES, "PIC time is logged in a simulator")
            self._add_conditional_issue(self._as_float(flight.sic_time) > 0, LintOptions.SIM_ISSUES, "SIC time is logged in a simulator")
            self._add_conditional_issue(self._as_float(flight.imc) > 0, LintOptions.SIM_ISSUES, "Actual IMC is logged in a simulator")
            self._add_conditional_issue(self._as_float(flight.cross_country) > 0, LintOptions.SIM_ISSUES, "Cross-country time is logged in a simulator")
            self._add_conditional_issue(not sim_registration, LintOptions.SIM_ISSUES, "Simulator flight is missing a device identifier")
        else:
            self._add_conditional_issue(ground_sim > 0, LintOptions.SIM_ISSUES, "Ground simulator time is logged in a real aircraft")
            self._add_conditional_issue(sim_registration, LintOptions.SIM_ISSUES, "Real aircraft flight includes a simulator registration")

    def _check_ifr_issues(self, flight: Flight, aircraft: Aircraft, model: MakeModel) -> None:
        approaches = self._as_int(getattr(flight, "approaches", 0))
        remarks = (getattr(flight, "remarks", "") or "").lower()
        has_approach_description = any(keyword in remarks for keyword in ("ils", "vor", "rnav", "gps", "loc", "approach"))
        has_hold_or_intercept = self._has_hold_or_intercept(flight)
        has_safety_pilot = bool(
            getattr(flight, "safety_pilot", None)
            or getattr(flight, "safety_pilot_name", None)
            or getattr(flight, "examiner_name", None)
            or self._as_float(getattr(flight, "dual_received", 0.0)) > 0
        )
        is_real_aircraft = not self._is_simulator(aircraft, model)

        self._add_conditional_issue(
            approaches > 0 and not has_approach_description,
            LintOptions.IFR_ISSUES,
            "Approaches are logged without an approach description",
        )
        self._add_conditional_issue(
            self._as_float(getattr(flight, "simulated_instrument", 0.0)) > 0 and is_real_aircraft and not has_safety_pilot,
            LintOptions.IFR_ISSUES,
            "Simulated IFR in a real aircraft should include a safety pilot or instructor",
        )
        self._add_conditional_issue(
            (approaches > 0 or has_hold_or_intercept)
            and self._as_float(getattr(flight, "simulated_instrument", 0.0)) + self._as_float(getattr(flight, "imc", 0.0)) == 0,
            LintOptions.IFR_ISSUES,
            "Approaches or holding/intercepting are logged without instrument time",
        )

    def _check_time_issues(self, flight: Flight, aircraft: Aircraft, model: MakeModel) -> None:
        total_time = self._as_float(getattr(flight, "total_time", 0.0))
        if total_time <= 0:
            return

        fields = {
            "PIC time": getattr(flight, "pic_time", 0.0),
            "SIC time": getattr(flight, "sic_time", 0.0),
            "Dual given": getattr(flight, "dual_given", 0.0),
            "Dual received": getattr(flight, "dual_received", 0.0),
            "Cross-country time": getattr(flight, "cross_country", 0.0),
            "Night time": getattr(flight, "night", 0.0),
            "Actual instrument time": getattr(flight, "imc", 0.0),
            "Simulated instrument time": getattr(flight, "simulated_instrument", 0.0),
        }

        for label, value in fields.items():
            self._add_conditional_issue(
                self._as_float(value) > total_time,
                LintOptions.TIME_ISSUES,
                f"{label} exceeds total flight time",
            )

    async def _check_airport_issues(self, flight: Flight, aircraft: Aircraft, model: MakeModel) -> None:
        codes = RouteParser.split_codes(getattr(flight, "route", "") or "")
        if not codes:
            return

        airports = await AirportQueryService.airports_matching_codes(codes)
        self._apply_airport_issues(flight, aircraft, model, codes, airports)

    def _check_misc_issues(self, flight: Flight, aircraft: Aircraft, model: MakeModel) -> None:
        water_operations = self._as_int(getattr(flight, "water_landings", 0)) + self._as_int(getattr(flight, "water_takeoffs", 0))
        category_class = self._category_class_id(aircraft, model)
        is_land_plane = category_class in {CatClassID.ASEL, CatClassID.AMEL}

        self._add_conditional_issue(
            water_operations > 0 and is_land_plane,
            LintOptions.MISC_ISSUES,
            "Water operations are logged in a land airplane",
        )
        self._add_conditional_issue(
            self._as_int(getattr(flight, "full_stop_landings_day", 0))
            + self._as_int(getattr(flight, "full_stop_landings_night", 0))
            > self._as_int(getattr(flight, "landings", 0)),
            LintOptions.MISC_ISSUES,
            "Described landings exceed total logged landings",
        )

    def _add_conditional_issue(self, condition: bool, option: LintOptions, description: str) -> None:
        if condition:
            self.current_issues.append(FlightIssue(area=option, issue_description=description))

    def _check_airport_issues_sync(self, flight: Flight, aircraft: Aircraft, model: MakeModel) -> None:
        airports = self._run_async(AirportQueryService.airports_matching_codes(RouteParser.split_codes(getattr(flight, "route", "") or "")))
        self._apply_airport_issues(
            flight,
            aircraft,
            model,
            RouteParser.split_codes(getattr(flight, "route", "") or ""),
            airports,
        )

    def _apply_airport_issues(
        self,
        flight: Flight,
        aircraft: Aircraft,
        model: MakeModel | None,
        codes: Sequence[str],
        airports: Sequence[object],
    ) -> None:
        if not codes:
            return

        airport_lookup = {getattr(airport, "code", "").upper(): airport for airport in airports}
        category_class = self._category_class_id(aircraft, model)

        for code in codes:
            normalized_code = code.upper()
            if normalized_code.startswith("@"):
                continue
            if normalized_code in {"LOCAL", "LCL"}:
                self.current_issues.append(
                    FlightIssue(area=LintOptions.AIRPORT_ISSUES, issue_description="Route contains LOCAL/LCL instead of a resolved airport")
                )
                continue

            airport = airport_lookup.get(normalized_code) or airport_lookup.get(RouteParser.us_prefix_convenience_alias(normalized_code))
            if airport is None:
                self.current_issues.append(
                    FlightIssue(area=LintOptions.AIRPORT_ISSUES, issue_description=f"Airport '{normalized_code}' could not be resolved")
                )
                continue

            facility_type = (getattr(airport, "facility_type", "") or "").upper()
            self._add_conditional_issue(
                category_class in {CatClassID.ASEL, CatClassID.AMEL} and facility_type == "S",
                LintOptions.AIRPORT_ISSUES,
                f"Land airplane route includes seaport '{normalized_code}'",
            )
            self._add_conditional_issue(
                category_class is not None and category_class.is_airplane and facility_type == "H",
                LintOptions.AIRPORT_ISSUES,
                f"Airplane route includes heliport '{normalized_code}'",
            )

        resolved_airports = [airport_lookup.get(code.upper()) or airport_lookup.get(RouteParser.us_prefix_convenience_alias(code.upper())) for code in codes]
        resolved_airports = [airport for airport in resolved_airports if airport is not None]
        if len(resolved_airports) >= 2 and self._as_float(getattr(flight, "total_time", 0.0)) > 0 and not self._is_simulator(aircraft, model):
            distance_nm = 0.0
            for departure, arrival in zip(resolved_airports, resolved_airports[1:]):
                distance_nm += LatLong(
                    float(getattr(departure, "latitude", 0.0)),
                    float(getattr(departure, "longitude", 0.0)),
                ).distance_from(
                    LatLong(
                        float(getattr(arrival, "latitude", 0.0)),
                        float(getattr(arrival, "longitude", 0.0)),
                    )
                )

            implied_speed = distance_nm / self._as_float(getattr(flight, "total_time", 0.0))
            engine_descriptor = getattr(model, "engine_type", None)
            if isinstance(engine_descriptor, enum.Enum):
                engine_name = engine_descriptor.name.lower()
            else:
                engine_name = str(engine_descriptor or getattr(aircraft, "engine_type", "") or "").lower()
            max_speed = 500.0 if "piston" in engine_name or not engine_name else 1000.0

            self._add_conditional_issue(
                implied_speed > max_speed,
                LintOptions.AIRPORT_ISSUES,
                f"Route implies an unlikely average speed of {implied_speed:.0f} knots",
            )

    @staticmethod
    def _run_async(coroutine):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coroutine)

        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coroutine)
        finally:
            loop.close()

    @staticmethod
    def _as_float(value: float | int | None) -> float:
        return float(value or 0.0)

    @staticmethod
    def _as_int(value: int | float | None) -> int:
        return int(value or 0)

    @staticmethod
    def _has_hold_or_intercept(flight: Flight) -> bool:
        for attr in ("holding_procedures", "holds", "hold_count", "intercepts", "intercepting"):
            value = getattr(flight, attr, None)
            if isinstance(value, bool) and value:
                return True
            if value:
                return True

        remarks = (getattr(flight, "remarks", "") or "").lower()
        return "hold" in remarks or "intercept" in remarks

    @staticmethod
    def _is_simulator(aircraft: Aircraft, model: MakeModel | None) -> bool:
        explicit_flags = [
            getattr(aircraft, "is_simulator", None),
            getattr(model, "is_simulator", None),
        ]
        for flag in explicit_flags:
            if isinstance(flag, bool):
                return flag

        allowed_types = getattr(model, "allowed_types", None)
        return allowed_types is not None and str(allowed_types).upper().endswith("SIMULATOR_ONLY")

    @staticmethod
    def _category_class_id(aircraft: Aircraft, model: MakeModel | None) -> CatClassID | None:
        candidates = [
            getattr(model, "category_class_id", None),
            getattr(aircraft, "category_class", None),
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
