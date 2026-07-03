from __future__ import annotations

import csv
import enum
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import StringIO
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from myflightbook_api.models.aircraft import Aircraft
from myflightbook_api.models.flight import Flight
from myflightbook_api.models.user import User

DATE_ALIASES = ("date", "flightdate")
TAIL_ALIASES = ("aircraftid", "aircraft", "aircraftregistration", "tail", "tailnumber", "registration")
FROM_ALIASES = ("from", "fromairport", "departureairport", "departure")
TO_ALIASES = ("to", "toairport", "arrivalairport", "arrival")
ROUTE_ALIASES = ("route", "routeofflight")
TOTAL_TIME_ALIASES = ("totaltime", "total", "flighttotaltime", "totalflighttime")
PIC_ALIASES = ("pic", "flightpic")
SIC_ALIASES = ("sic", "flightsic")
DUAL_GIVEN_ALIASES = ("dualgiven", "cfi")
DUAL_RECEIVED_ALIASES = ("dualreceived",)
CROSS_COUNTRY_ALIASES = ("crosscountry", "crosscountrytime")
NIGHT_ALIASES = ("night", "nighttime")
IMC_ALIASES = ("imc", "actualinstrument")
SIMULATED_INSTRUMENT_ALIASES = ("simulatedinstrument", "siminst")
LANDINGS_ALIASES = ("alllandings", "landings", "totallandings")
DAY_FULL_STOP_ALIASES = ("daylandingsfullstop", "fulllstoplandingsday", "fullstoplandingsday")
NIGHT_FULL_STOP_ALIASES = ("nightlandingsfullstop", "fullstoplandingsnight")
APPROACH_ALIASES = ("approaches", "instrumentapproaches")
REMARKS_ALIASES = ("remarks", "comments", "notes", "textcfinotes")


class ImportFormat(enum.Enum):
    GENERIC_CSV = "generic"
    FOREFLIGHT = "foreflight"
    LOGTEN_PRO = "logten_pro"
    CREW_LOUNGE = "crew_lounge"
    MCC_PILOT = "mcc_pilot"
    PILOT_PRO = "pilot_pro"
    ROSTER_BUSTER = "roster_buster"
    FLICA = "flica"


@dataclass
class ImportResult:
    success: bool
    imported_flights: list[Flight]
    error_messages: list[str]
    warning_messages: list[str]
    skipped_rows: int


def _clean(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_header(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


class BaseFlightImporter:
    """
    Base class for all third-party logbook importers.
    """

    def __init__(self, user: User, *, existing_aircraft: Sequence[Aircraft] | None = None):
        self.user = user
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.imported_flights: list[Flight] = []
        self.skipped_rows: int = 0
        self._aircraft_by_tail: dict[str, Aircraft] = {}
        for aircraft in existing_aircraft or ():
            normalized_tail = _clean(getattr(aircraft, "tail_number", "")).upper()
            if normalized_tail:
                self._aircraft_by_tail[normalized_tail] = aircraft

    def can_parse(self, header_row: list[str]) -> bool:
        raise NotImplementedError()

    def parse_file(self, file_content: str) -> ImportResult:
        raise NotImplementedError()

    def _add_error(self, row_num: int, message: str) -> None:
        self.errors.append(f"Row {row_num}: {message}")

    def _add_warning(self, row_num: int, message: str) -> None:
        self.warnings.append(f"Row {row_num}: {message}")

    def _reset(self) -> None:
        self.errors.clear()
        self.warnings.clear()
        self.imported_flights.clear()
        self.skipped_rows = 0

    def _detect_dialect(self, file_content: str) -> csv.Dialect:
        sample = file_content[:2048]
        try:
            return csv.Sniffer().sniff(sample, delimiters=",\t;")
        except csv.Error:
            return csv.get_dialect("excel")

    def _build_reader(self, file_content: str) -> tuple[list[str], csv.DictReader[str]]:
        dialect = self._detect_dialect(file_content)
        reader = csv.DictReader(StringIO(file_content), dialect=dialect)
        header_row = [field for field in reader.fieldnames or [] if field]
        return header_row, reader

    def _header_lookup(self, header_row: list[str]) -> dict[str, str]:
        return {_normalize_header(header): header for header in header_row}

    def _get_row_value(self, row: dict[str, str | None], header_lookup: dict[str, str], aliases: Sequence[str]) -> str:
        for alias in aliases:
            actual_header = header_lookup.get(alias)
            if actual_header is None:
                continue
            value = row.get(actual_header)
            cleaned_value = _clean(value)
            if cleaned_value:
                return cleaned_value
        return ""

    def _parse_date(self, value: str) -> date:
        cleaned_value = _clean(value)
        if not cleaned_value:
            raise ValueError("flight date is required")

        for date_format in (
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%m/%d/%Y",
            "%m/%d/%y",
            "%Y-%m-%d %H:%M:%S",
            "%m/%d/%Y %H:%M",
            "%Y-%m-%dT%H:%M:%S",
        ):
            try:
                parsed_value = datetime.strptime(cleaned_value, date_format)
            except ValueError:
                continue
            return parsed_value.date()

        try:
            return datetime.fromisoformat(cleaned_value).date()
        except ValueError as exc:
            raise ValueError(f"unsupported flight date {cleaned_value!r}") from exc

    def _parse_decimal_hours(self, value: str) -> Decimal:
        cleaned_value = _clean(value)
        if not cleaned_value:
            return Decimal("0")

        normalized_value = cleaned_value.replace(",", ".")
        if ":" in normalized_value:
            hours_text, minutes_text = normalized_value.split(":", maxsplit=1)
            try:
                hours = int(hours_text)
                minutes = Decimal(minutes_text)
            except (InvalidOperation, ValueError) as exc:
                raise ValueError(f"invalid time value {cleaned_value!r}") from exc
            return Decimal(hours) + (minutes / Decimal("60"))

        try:
            return Decimal(normalized_value)
        except InvalidOperation as exc:
            raise ValueError(f"invalid numeric value {cleaned_value!r}") from exc

    def _parse_int(self, value: str) -> int:
        return int(self._parse_decimal_hours(value))

    def _build_route(self, row: dict[str, str | None], header_lookup: dict[str, str]) -> str:
        explicit_route = self._get_row_value(row, header_lookup, ROUTE_ALIASES)
        if explicit_route:
            return explicit_route

        origin = self._get_row_value(row, header_lookup, FROM_ALIASES)
        destination = self._get_row_value(row, header_lookup, TO_ALIASES)
        if origin and destination:
            return f"{origin}-{destination}"
        if origin:
            return origin
        return destination

    def _resolve_aircraft(self, tail_number: str) -> Aircraft:
        normalized_tail = _clean(tail_number).upper() or "UNKNOWN"
        aircraft = self._aircraft_by_tail.get(normalized_tail)
        if aircraft is not None:
            return aircraft

        aircraft = Aircraft(
            owner_user_id=self.user.id,
            tail_number=normalized_tail,
            display_name=normalized_tail,
        )
        self._aircraft_by_tail[normalized_tail] = aircraft
        return aircraft

    def _build_flight(
        self,
        *,
        aircraft: Aircraft,
        flight_date: date,
        route: str,
        remarks: str | None,
        total_time: Decimal,
        pic_time: Decimal,
        sic_time: Decimal,
        dual_given: Decimal,
        dual_received: Decimal,
        cross_country: Decimal,
        night: Decimal,
        imc: Decimal,
        simulated_instrument: Decimal,
        landings: int,
        full_stop_landings_day: int,
        full_stop_landings_night: int,
        approaches: int,
    ) -> Flight:
        payload = {
            "user_id": self.user.id,
            "flight_date": flight_date,
            "route": route,
            "remarks": remarks,
            "total_time": total_time,
            "pic_time": pic_time,
            "sic_time": sic_time,
            "dual_given": dual_given,
            "dual_received": dual_received,
            "cross_country": cross_country,
            "night": night,
            "imc": imc,
            "simulated_instrument": simulated_instrument,
            "landings": landings,
            "full_stop_landings_day": full_stop_landings_day,
            "full_stop_landings_night": full_stop_landings_night,
            "approaches": approaches,
        }

        if getattr(aircraft, "id", None) is None:
            payload["aircraft"] = aircraft
        else:
            payload["aircraft_id"] = aircraft.id

        return Flight(**payload)

    def _result(self) -> ImportResult:
        return ImportResult(
            success=not self.errors,
            imported_flights=list(self.imported_flights),
            error_messages=list(self.errors),
            warning_messages=list(self.warnings),
            skipped_rows=self.skipped_rows,
        )


class ForeFlightImporter(BaseFlightImporter):
    def can_parse(self, header_row: list[str]) -> bool:
        normalized_headers = {_normalize_header(header) for header in header_row}
        return "textcfinotes" in normalized_headers or {
            "aircraftid",
            "totaltime",
            "crosscountry",
        }.issubset(normalized_headers)

    def parse_file(self, file_content: str) -> ImportResult:
        self._reset()
        header_row, reader = self._build_reader(file_content)
        header_lookup = self._header_lookup(header_row)

        for row_num, row in enumerate(reader, start=2):
            if not any(_clean(value) for value in row.values()):
                continue

            try:
                aircraft = self._resolve_aircraft(self._get_row_value(row, header_lookup, TAIL_ALIASES))
                flight = self._build_flight(
                    aircraft=aircraft,
                    flight_date=self._parse_date(self._get_row_value(row, header_lookup, DATE_ALIASES)),
                    route=self._build_route(row, header_lookup),
                    remarks=self._get_row_value(row, header_lookup, REMARKS_ALIASES) or None,
                    total_time=self._parse_decimal_hours(self._get_row_value(row, header_lookup, TOTAL_TIME_ALIASES)),
                    pic_time=self._parse_decimal_hours(self._get_row_value(row, header_lookup, PIC_ALIASES)),
                    sic_time=self._parse_decimal_hours(self._get_row_value(row, header_lookup, SIC_ALIASES)),
                    dual_given=self._parse_decimal_hours(self._get_row_value(row, header_lookup, DUAL_GIVEN_ALIASES)),
                    dual_received=self._parse_decimal_hours(self._get_row_value(row, header_lookup, DUAL_RECEIVED_ALIASES)),
                    cross_country=self._parse_decimal_hours(self._get_row_value(row, header_lookup, CROSS_COUNTRY_ALIASES)),
                    night=self._parse_decimal_hours(self._get_row_value(row, header_lookup, NIGHT_ALIASES)),
                    imc=self._parse_decimal_hours(self._get_row_value(row, header_lookup, IMC_ALIASES)),
                    simulated_instrument=self._parse_decimal_hours(
                        self._get_row_value(row, header_lookup, SIMULATED_INSTRUMENT_ALIASES)
                    ),
                    landings=self._parse_int(self._get_row_value(row, header_lookup, LANDINGS_ALIASES)),
                    full_stop_landings_day=self._parse_int(
                        self._get_row_value(row, header_lookup, DAY_FULL_STOP_ALIASES)
                    ),
                    full_stop_landings_night=self._parse_int(
                        self._get_row_value(row, header_lookup, NIGHT_FULL_STOP_ALIASES)
                    ),
                    approaches=self._parse_int(self._get_row_value(row, header_lookup, APPROACH_ALIASES)),
                )
            except ValueError as exc:
                self._add_error(row_num, str(exc))
                self.skipped_rows += 1
                continue

            self.imported_flights.append(flight)

        return self._result()


class LogTenProImporter(BaseFlightImporter):
    def can_parse(self, header_row: list[str]) -> bool:
        normalized_headers = {_normalize_header(header) for header in header_row}
        return {"flightdate", "flighttotaltime"}.issubset(normalized_headers)

    def parse_file(self, file_content: str) -> ImportResult:
        self._reset()
        header_row, reader = self._build_reader(file_content)
        header_lookup = self._header_lookup(header_row)

        for row_num, row in enumerate(reader, start=2):
            if not any(_clean(value) for value in row.values()):
                continue

            try:
                aircraft = self._resolve_aircraft(self._get_row_value(row, header_lookup, TAIL_ALIASES))
                flight = self._build_flight(
                    aircraft=aircraft,
                    flight_date=self._parse_date(self._get_row_value(row, header_lookup, DATE_ALIASES)),
                    route=self._build_route(row, header_lookup),
                    remarks=self._get_row_value(row, header_lookup, REMARKS_ALIASES) or None,
                    total_time=self._parse_decimal_hours(self._get_row_value(row, header_lookup, TOTAL_TIME_ALIASES)),
                    pic_time=self._parse_decimal_hours(self._get_row_value(row, header_lookup, PIC_ALIASES)),
                    sic_time=self._parse_decimal_hours(self._get_row_value(row, header_lookup, SIC_ALIASES)),
                    dual_given=self._parse_decimal_hours(self._get_row_value(row, header_lookup, DUAL_GIVEN_ALIASES)),
                    dual_received=self._parse_decimal_hours(self._get_row_value(row, header_lookup, DUAL_RECEIVED_ALIASES)),
                    cross_country=self._parse_decimal_hours(self._get_row_value(row, header_lookup, CROSS_COUNTRY_ALIASES)),
                    night=self._parse_decimal_hours(self._get_row_value(row, header_lookup, NIGHT_ALIASES)),
                    imc=self._parse_decimal_hours(self._get_row_value(row, header_lookup, IMC_ALIASES)),
                    simulated_instrument=self._parse_decimal_hours(
                        self._get_row_value(row, header_lookup, SIMULATED_INSTRUMENT_ALIASES)
                    ),
                    landings=self._parse_int(self._get_row_value(row, header_lookup, LANDINGS_ALIASES)),
                    full_stop_landings_day=self._parse_int(
                        self._get_row_value(row, header_lookup, DAY_FULL_STOP_ALIASES)
                    ),
                    full_stop_landings_night=self._parse_int(
                        self._get_row_value(row, header_lookup, NIGHT_FULL_STOP_ALIASES)
                    ),
                    approaches=self._parse_int(self._get_row_value(row, header_lookup, APPROACH_ALIASES)),
                )
            except ValueError as exc:
                self._add_error(row_num, str(exc))
                self.skipped_rows += 1
                continue

            self.imported_flights.append(flight)

        return self._result()


class GenericCSVImporter(BaseFlightImporter):
    def can_parse(self, header_row: list[str]) -> bool:
        normalized_headers = {_normalize_header(header) for header in header_row}
        has_date = any(alias in normalized_headers for alias in DATE_ALIASES)
        has_total = any(alias in normalized_headers for alias in TOTAL_TIME_ALIASES)
        return has_date and has_total

    def parse_file(self, file_content: str) -> ImportResult:
        self._reset()
        header_row, reader = self._build_reader(file_content)
        header_lookup = self._header_lookup(header_row)

        for row_num, row in enumerate(reader, start=2):
            if not any(_clean(value) for value in row.values()):
                continue

            try:
                aircraft = self._resolve_aircraft(self._get_row_value(row, header_lookup, TAIL_ALIASES))
                flight = self._build_flight(
                    aircraft=aircraft,
                    flight_date=self._parse_date(self._get_row_value(row, header_lookup, DATE_ALIASES)),
                    route=self._build_route(row, header_lookup),
                    remarks=self._get_row_value(row, header_lookup, REMARKS_ALIASES) or None,
                    total_time=self._parse_decimal_hours(self._get_row_value(row, header_lookup, TOTAL_TIME_ALIASES)),
                    pic_time=self._parse_decimal_hours(self._get_row_value(row, header_lookup, PIC_ALIASES)),
                    sic_time=self._parse_decimal_hours(self._get_row_value(row, header_lookup, SIC_ALIASES)),
                    dual_given=self._parse_decimal_hours(self._get_row_value(row, header_lookup, DUAL_GIVEN_ALIASES)),
                    dual_received=self._parse_decimal_hours(self._get_row_value(row, header_lookup, DUAL_RECEIVED_ALIASES)),
                    cross_country=self._parse_decimal_hours(self._get_row_value(row, header_lookup, CROSS_COUNTRY_ALIASES)),
                    night=self._parse_decimal_hours(self._get_row_value(row, header_lookup, NIGHT_ALIASES)),
                    imc=self._parse_decimal_hours(self._get_row_value(row, header_lookup, IMC_ALIASES)),
                    simulated_instrument=self._parse_decimal_hours(
                        self._get_row_value(row, header_lookup, SIMULATED_INSTRUMENT_ALIASES)
                    ),
                    landings=self._parse_int(self._get_row_value(row, header_lookup, LANDINGS_ALIASES)),
                    full_stop_landings_day=self._parse_int(
                        self._get_row_value(row, header_lookup, DAY_FULL_STOP_ALIASES)
                    ),
                    full_stop_landings_night=self._parse_int(
                        self._get_row_value(row, header_lookup, NIGHT_FULL_STOP_ALIASES)
                    ),
                    approaches=self._parse_int(self._get_row_value(row, header_lookup, APPROACH_ALIASES)),
                )
            except ValueError as exc:
                self._add_error(row_num, str(exc))
                self.skipped_rows += 1
                continue

            self.imported_flights.append(flight)

        return self._result()


class ImportOrchestratorService:
    IMPORTERS = (ForeFlightImporter, LogTenProImporter, GenericCSVImporter)

    @staticmethod
    def _extract_header(file_content: str) -> list[str]:
        first_non_empty_line = next((line for line in file_content.splitlines() if line.strip()), "")
        if not first_non_empty_line:
            return []
        try:
            dialect = csv.Sniffer().sniff(first_non_empty_line, delimiters=",\t;")
        except csv.Error:
            dialect = csv.get_dialect("excel")
        return next(csv.reader([first_non_empty_line], dialect=dialect), [])

    @classmethod
    async def import_flights_from_csv(
        cls,
        file_content: str,
        user: User,
        session: AsyncSession,
    ) -> ImportResult:
        header_row = cls._extract_header(file_content)
        if not header_row:
            return ImportResult(
                success=False,
                imported_flights=[],
                error_messages=["Unable to read a CSV header row from the uploaded file."],
                warning_messages=[],
                skipped_rows=0,
            )

        existing_aircraft_result = await session.execute(
            select(Aircraft).where(Aircraft.owner_user_id == user.id).order_by(Aircraft.tail_number.asc())
        )
        existing_aircraft = existing_aircraft_result.scalars().all()

        importer: BaseFlightImporter | None = None
        for importer_cls in cls.IMPORTERS:
            candidate = importer_cls(user, existing_aircraft=existing_aircraft)
            if candidate.can_parse(header_row):
                importer = candidate
                break

        if importer is None:
            return ImportResult(
                success=False,
                imported_flights=[],
                error_messages=["No supported import format matched the uploaded CSV header."],
                warning_messages=[],
                skipped_rows=0,
            )

        result = importer.parse_file(file_content)
        transient_aircraft: dict[int, Aircraft] = {}
        for flight in result.imported_flights:
            aircraft = flight.aircraft
            if aircraft is None or getattr(aircraft, "id", None) is not None:
                continue
            transient_aircraft[id(aircraft)] = aircraft

        for aircraft in transient_aircraft.values():
            session.add(aircraft)
        for flight in result.imported_flights:
            session.add(flight)

        await session.commit()
        for flight in result.imported_flights:
            await session.refresh(flight)

        return result
