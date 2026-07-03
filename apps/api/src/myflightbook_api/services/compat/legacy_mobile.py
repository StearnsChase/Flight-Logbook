from __future__ import annotations

import base64
import hashlib
import hmac
import html

from collections import Counter
from collections.abc import Awaitable, Callable, Collection, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import IntEnum
from typing import Protocol
from uuid import UUID, uuid4
from xml.sax.saxutils import escape

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from myflightbook_api.models.aircraft import Aircraft
from myflightbook_api.models.country_code import CountryCodePrefix
from myflightbook_api.models.deadline import Deadline
from myflightbook_api.models.flight import Flight
from myflightbook_api.models.legacy import LegacyEntityMapping
from myflightbook_api.models.make_model import MakeModel, Manufacturer
from myflightbook_api.models.media import ImageAsset
from myflightbook_api.models.user import User
from myflightbook_api.services.aircraft.user_aircraft import UserAircraftService
from myflightbook_api.services.currency.tracker import CurrencyStatusItem, CurrencyTrackerService
from myflightbook_api.services.flights.lint import FlightLint, LintOptions
from myflightbook_api.services.geography.airports import RouteParser
from myflightbook_api.services.geography.latlong import LatLong
from myflightbook_api.services.media.storage import delete_object as delete_media_object
from myflightbook_api.services.totals import summarize_flights


_DOTNET_TICKS_PER_SECOND = 10_000_000
_DOTNET_TICKS_PER_MICROSECOND = 10
_DOTNET_EPOCH = datetime(1, 1, 1, tzinfo=timezone.utc)
_DEFAULT_TOKEN_SIGNING_KEY = "legacy-mobile-dev-key"
_LEGACY_MOBILE_IMAGE_SYSTEM = "myflightbook-mobile"
_LEGACY_MOBILE_IMAGE_TABLE = "MFBImageInfo"
_LEGACY_IMAGE_ENTITY_TYPE = "image_asset"


class LegacyMobileCompatibilityError(Exception):
    """Base error for legacy mobile compatibility behavior."""


class LegacyMobileAuthenticationError(LegacyMobileCompatibilityError):
    """Raised when a legacy auth token or second factor cannot be validated."""


class LegacyMobileAuthorizationError(LegacyMobileCompatibilityError):
    """Raised when a user attempts an unsupported emulation flow."""


class LegacyAuthStatus(IntEnum):
    Failed = 0
    TwoFactorCodeRequired = 1
    Success = 2


@dataclass(frozen=True, slots=True)
class LegacyAuthResult:
    result: LegacyAuthStatus = LegacyAuthStatus.Failed
    auth_token: str | None = None

    def to_legacy_payload(self) -> dict[str, str | None]:
        return {
            "Result": self.result.name,
            "AuthToken": self.auth_token,
        }


@dataclass(frozen=True, slots=True)
class LegacyAuthTokenPayload:
    username: str
    issued_ticks: int
    issued_at: datetime


@dataclass(frozen=True, slots=True)
class LegacyMobileUserRecord:
    username: str
    email: str | None = None
    last_password_change: datetime | None = None
    can_support: bool = False
    can_manage_data: bool = False
    two_factor_secret: str | None = None


@dataclass(frozen=True, slots=True)
class _IssuedLegacyAuthToken:
    auth_token: str
    token_user: LegacyMobileUserRecord
    authenticating_user: LegacyMobileUserRecord


def _normalize_optional_utc_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.year <= 1:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class LegacyAircraftMaintenanceSnapshot:
    last_altimeter: datetime | None = None
    last_vor: datetime | None = None
    last_static: datetime | None = None
    last_transponder: datetime | None = None
    last_annual: datetime | None = None
    last_elt: datetime | None = None
    registration_due: datetime | None = None

    def normalized(self) -> LegacyAircraftMaintenanceSnapshot:
        return LegacyAircraftMaintenanceSnapshot(
            last_altimeter=_normalize_optional_utc_datetime(self.last_altimeter),
            last_vor=_normalize_optional_utc_datetime(self.last_vor),
            last_static=_normalize_optional_utc_datetime(self.last_static),
            last_transponder=_normalize_optional_utc_datetime(self.last_transponder),
            last_annual=_normalize_optional_utc_datetime(self.last_annual),
            last_elt=_normalize_optional_utc_datetime(self.last_elt),
            registration_due=_normalize_optional_utc_datetime(self.registration_due),
        )


@dataclass(frozen=True, slots=True)
class LegacyAircraftRecord:
    aircraft_id: str
    tail_number: str
    display_name: str
    model_name: str | None = None
    category_class: str | None = None
    engine_type: str | None = None
    is_complex: bool = False
    is_high_performance: bool = False
    is_retractable: bool = False
    maintenance: LegacyAircraftMaintenanceSnapshot = field(default_factory=LegacyAircraftMaintenanceSnapshot)
    public_notes: str | None = None
    private_notes: str | None = None
    user_flags: int = 0
    revision: int = 0
    is_anonymous: bool = False

    def to_legacy_payload(self) -> dict[str, object]:
        return {
            "AircraftID": self.aircraft_id,
            "TailNumber": self.tail_number,
            "DisplayName": self.display_name,
            "ModelName": self.model_name,
            "CategoryClass": self.category_class,
            "EngineType": self.engine_type,
            "IsComplex": self.is_complex,
            "IsHighPerformance": self.is_high_performance,
            "IsRetractable": self.is_retractable,
            "IsAnonymous": self.is_anonymous,
            "LastAltimeter": self.maintenance.last_altimeter,
            "LastVOR": self.maintenance.last_vor,
            "LastStatic": self.maintenance.last_static,
            "LastTransponder": self.maintenance.last_transponder,
            "LastAnnual": self.maintenance.last_annual,
            "LastELT": self.maintenance.last_elt,
            "RegistrationDue": self.maintenance.registration_due,
            "PublicNotes": self.public_notes,
            "PrivateNotes": self.private_notes,
            "Flags": self.user_flags,
            "Revision": self.revision,
        }


class LegacyAircraftContract:
    REAL_AIRCRAFT_INSTANCE_TYPE = 1

    def __init__(self, compatibility_service: LegacyMobileCompatibilityService) -> None:
        self._compatibility_service = compatibility_service

    def aircraft_for_user(
        self,
        auth_token: str,
        aircraft: Sequence[Aircraft],
        *,
        anonymous_tail_overrides: Mapping[str, str] | None = None,
        maintenance_overrides: Mapping[str, LegacyAircraftMaintenanceSnapshot] | None = None,
    ) -> list[LegacyAircraftRecord] | None:
        username = self._compatibility_service.get_encrypted_user(auth_token)
        if not username:
            return None

        return [
            self._to_legacy_aircraft_record(
                item,
                anonymous_tail_override=(anonymous_tail_overrides or {}).get(str(item.id)),
                maintenance_override=(maintenance_overrides or {}).get(str(item.id)),
            )
            for item in aircraft
        ]

    async def add_aircraft_for_user(
        self,
        auth_token: str,
        *,
        owner_user_id: str,
        tail_number: str,
        model_id: int,
        instance_type_id: int,
        session: AsyncSession,
        make_model: MakeModel,
        manufacturer: Manufacturer | None = None,
        country_codes: Sequence[CountryCodePrefix] | None = None,
        current_aircraft: Sequence[Aircraft] = (),
        anonymous_tail_resolver: Callable[[int], str] | None = None,
        simulator_tail_resolver: Callable[[int, int], str] | None = None,
        anonymous_tail_overrides: Mapping[str, str] | None = None,
    ) -> list[LegacyAircraftRecord]:
        self._require_authenticated_user(auth_token)

        if make_model.id != model_id:
            raise LegacyMobileCompatibilityError("Make/model lookup did not match the requested model id")
        if instance_type_id < self.REAL_AIRCRAFT_INSTANCE_TYPE:
            raise LegacyMobileCompatibilityError("Instance type is out of range")

        resolved_tail = (tail_number or "").strip()
        if instance_type_id != self.REAL_AIRCRAFT_INSTANCE_TYPE:
            if simulator_tail_resolver is None:
                raise LegacyMobileCompatibilityError(
                    "Legacy simulator aircraft creation requires a simulator tail resolver"
                )
            resolved_tail = simulator_tail_resolver(model_id, instance_type_id)
        elif resolved_tail.startswith(CountryCodePrefix.ANON_PREFIX):
            if anonymous_tail_resolver is None:
                raise LegacyMobileCompatibilityError(
                    "Legacy anonymous aircraft creation requires an anonymous tail resolver"
                )
            resolved_tail = anonymous_tail_resolver(model_id)

        aircraft_service = UserAircraftService(session)
        created = await aircraft_service.create_user_aircraft(
            owner_user_id=owner_user_id,
            tail_number=resolved_tail,
            make_model=make_model,
            manufacturer=manufacturer,
            country_codes=country_codes,
        )

        return self.aircraft_for_user(
            auth_token,
            [*current_aircraft, created],
            anonymous_tail_overrides=anonymous_tail_overrides,
        ) or []

    def aircraft_matching_prefix(
        self,
        auth_token: str,
        prefix: str,
        aircraft: Sequence[Aircraft],
        *,
        anonymous_tail_overrides: Mapping[str, str] | None = None,
        maintenance_overrides: Mapping[str, LegacyAircraftMaintenanceSnapshot] | None = None,
    ) -> list[LegacyAircraftRecord]:
        self._require_authenticated_user(auth_token)
        if not prefix or not prefix.strip():
            return []

        search_prefix = UserAircraftService.normalize_tail_for_search(prefix)
        return [
            self._to_legacy_aircraft_record(
                item,
                anonymous_tail_override=(anonymous_tail_overrides or {}).get(str(item.id)),
                maintenance_override=(maintenance_overrides or {}).get(str(item.id)),
            )
            for item in aircraft
            if UserAircraftService.normalize_tail_for_search(item.tail_number).startswith(search_prefix)
        ]

    def update_maintenance_for_aircraft(
        self,
        auth_token: str,
        aircraft: Aircraft,
        payload: LegacyAircraftRecord,
        *,
        update_flags: bool = False,
        update_notes: bool = False,
    ) -> LegacyAircraftRecord:
        self._require_authenticated_user(auth_token)
        if payload.revision < 0:
            raise LegacyMobileCompatibilityError("Aircraft revision is too old to edit")
        if aircraft.revision != payload.revision:
            raise LegacyMobileCompatibilityError("Aircraft is not the most recent revision")

        normalized_maintenance = payload.maintenance.normalized()
        aircraft.last_altimeter = normalized_maintenance.last_altimeter
        aircraft.last_vor = normalized_maintenance.last_vor
        aircraft.last_static = normalized_maintenance.last_static
        aircraft.last_transponder = normalized_maintenance.last_transponder
        aircraft.last_annual = normalized_maintenance.last_annual
        aircraft.last_elt = normalized_maintenance.last_elt
        aircraft.registration_due = normalized_maintenance.registration_due

        if update_notes:
            aircraft.public_notes = payload.public_notes
            aircraft.private_notes = payload.private_notes
        if update_flags:
            aircraft.user_flags = payload.user_flags

        aircraft.revision += 1
        return self._to_legacy_aircraft_record(
            aircraft,
            maintenance_override=normalized_maintenance,
        )

    def delete_aircraft_for_user(
        self,
        auth_token: str,
        aircraft_id: str,
        aircraft: Sequence[Aircraft],
        *,
        anonymous_tail_overrides: Mapping[str, str] | None = None,
        maintenance_overrides: Mapping[str, LegacyAircraftMaintenanceSnapshot] | None = None,
    ) -> list[LegacyAircraftRecord]:
        self._require_authenticated_user(auth_token)
        remaining = [item for item in aircraft if str(item.id) != str(aircraft_id)]
        return [
            self._to_legacy_aircraft_record(
                item,
                anonymous_tail_override=(anonymous_tail_overrides or {}).get(str(item.id)),
                maintenance_override=(maintenance_overrides or {}).get(str(item.id)),
            )
            for item in remaining
        ]

    def _require_authenticated_user(self, auth_token: str) -> str:
        username = self._compatibility_service.get_encrypted_user(auth_token)
        if not username:
            raise LegacyMobileAuthenticationError("Bad auth")
        return username

    @staticmethod
    def _to_legacy_aircraft_record(
        aircraft: Aircraft,
        *,
        anonymous_tail_override: str | None = None,
        maintenance_override: LegacyAircraftMaintenanceSnapshot | None = None,
    ) -> LegacyAircraftRecord:
        return LegacyAircraftRecord(
            aircraft_id=str(aircraft.id),
            tail_number=anonymous_tail_override or aircraft.tail_number,
            display_name=aircraft.display_name,
            model_name=aircraft.model_name,
            category_class=aircraft.category_class,
            engine_type=aircraft.engine_type,
            is_complex=aircraft.is_complex,
            is_high_performance=aircraft.is_high_performance,
            is_retractable=aircraft.is_retractable,
            maintenance=(
                maintenance_override
                or LegacyAircraftMaintenanceSnapshot(
                    last_altimeter=aircraft.last_altimeter,
                    last_vor=aircraft.last_vor,
                    last_static=aircraft.last_static,
                    last_transponder=aircraft.last_transponder,
                    last_annual=aircraft.last_annual,
                    last_elt=aircraft.last_elt,
                    registration_due=aircraft.registration_due,
                )
            ).normalized(),
            public_notes=aircraft.public_notes,
            private_notes=aircraft.private_notes,
            user_flags=aircraft.user_flags,
            revision=aircraft.revision,
            is_anonymous=anonymous_tail_override is not None,
        )


@dataclass(frozen=True, slots=True)
class LegacyFlightQuery:
    date_min: date | datetime | None = None
    date_max: date | datetime | None = None
    route_contains: str | None = None


@dataclass(frozen=True, slots=True)
class LegacyTotalsItem:
    key: str
    label: str
    value: float | int

    def to_legacy_payload(self) -> dict[str, object]:
        return {"Key": self.key, "Label": self.label, "Value": self.value}


@dataclass(frozen=True, slots=True)
class LegacyVisitedAirport:
    code: str
    visits: int

    def to_legacy_payload(self) -> dict[str, object]:
        return {"Code": self.code, "Visits": self.visits}


class LegacyLogbookContract:
    def __init__(self, compatibility_service: LegacyMobileCompatibilityService) -> None:
        self._compatibility_service = compatibility_service

    def get_currency_for_user(
        self,
        auth_token: str,
        flights: Sequence[Flight],
        *,
        deadlines: Sequence[Deadline] = (),
    ) -> list[CurrencyStatusItem] | None:
        username = self._decode_user_or_none(auth_token)
        if username is None:
            return None

        return [
            CurrencyTrackerService.compute_night_currency(flights),
            CurrencyTrackerService.compute_ifr_currency(flights),
            *CurrencyTrackerService.get_currency_status_for_deadlines(deadlines),
        ]

    def totals_for_user(
        self,
        auth_token: str,
        flights: Sequence[Flight],
        dt_min: date | datetime,
    ) -> list[LegacyTotalsItem] | None:
        username = self._decode_user_or_none(auth_token)
        if username is None:
            return None

        min_date = self._coerce_date(dt_min)
        filtered = [flight for flight in flights if self._coerce_date(getattr(flight, "flight_date", None)) >= min_date]
        return self._summary_to_legacy_items(summarize_flights(filtered))

    def totals_for_user_with_query(
        self,
        auth_token: str,
        flights: Sequence[Flight],
        query: LegacyFlightQuery | None = None,
    ) -> list[LegacyTotalsItem] | None:
        username = self._decode_user_or_none(auth_token)
        if username is None:
            return None

        filtered = self._filter_flights(flights, query)
        return self._summary_to_legacy_items(summarize_flights(filtered))

    def visited_airports(
        self,
        auth_token: str,
        flights: Sequence[Flight],
    ) -> list[LegacyVisitedAirport] | None:
        username = self._decode_user_or_none(auth_token)
        if username is None:
            return None

        counts = Counter[str]()
        for flight in flights:
            for code in RouteParser.split_codes(getattr(flight, "route", "") or ""):
                if code.startswith("@") or code in {"LOCAL", "LCL"}:
                    continue
                counts[code] += 1

        return [LegacyVisitedAirport(code=code, visits=counts[code]) for code in sorted(counts)]

    def flights_with_query(
        self,
        auth_token: str,
        flights: Sequence[Flight],
        *,
        query: LegacyFlightQuery | None = None,
        offset: int = 0,
        max_count: int = -1,
    ) -> list[Flight]:
        self._require_authenticated_user(auth_token)
        filtered = self._filter_flights(flights, query)
        if offset > 0:
            filtered = filtered[offset:]
        if max_count >= 0:
            filtered = filtered[:max_count]
        return filtered

    def check_flight(self, auth_token: str, flight: Flight) -> list[str]:
        self._require_authenticated_user(auth_token)
        lint = FlightLint()
        issues = lint.check_flights([flight], LintOptions.default_options())
        return [issue.issue_description for grouped in issues for issue in grouped.issues]

    def flight_path_for_flight(
        self,
        auth_token: str,
        flight_id: str,
        *,
        flight_paths: Mapping[str, Sequence[LatLong]],
    ) -> list[LatLong] | None:
        self._require_authenticated_user(auth_token)
        path = flight_paths.get(str(flight_id))
        if not path:
            return None
        return [LatLong(point) for point in path]

    def flight_path_for_flight_gpx(
        self,
        auth_token: str,
        flight_id: str,
        *,
        flight_paths: Mapping[str, Sequence[LatLong]],
    ) -> str | None:
        path = self.flight_path_for_flight(auth_token, flight_id, flight_paths=flight_paths)
        if not path:
            return None

        track_points = "".join(
            f'<trkpt lat="{point.latitude:.8f}" lon="{point.longitude:.8f}"></trkpt>'
            for point in path
        )
        escaped_name = escape(str(flight_id))
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<gpx version="1.1" creator="MyFlightbook API" xmlns="http://www.topografix.com/GPX/1/1">'
            f"<trk><name>{escaped_name}</name><trkseg>{track_points}</trkseg></trk></gpx>"
        )

    def commit_flight_with_options(
        self,
        auth_token: str,
        flight: Flight,
        *,
        existing_flights: Sequence[Flight] = (),
    ) -> Flight:
        self._require_authenticated_user(auth_token)

        duplicate = next(
            (
                candidate
                for candidate in existing_flights
                if self._flight_signature(candidate) == self._flight_signature(flight)
            ),
            None,
        )
        if duplicate is not None:
            return duplicate

        now = datetime.now(timezone.utc)
        if getattr(flight, "id", None) is None:
            flight.id = uuid4()
        if getattr(flight, "created_at", None) is None:
            flight.created_at = now
        flight.updated_at = now
        return flight

    def create_pending_flight(
        self,
        auth_token: str,
        flight: Flight,
        *,
        pending_flights: Sequence[LegacyPendingFlight] = (),
    ) -> list[LegacyPendingFlight]:
        username = self._require_authenticated_user(auth_token)
        pending = LegacyPendingFlight(
            pending_id=str(uuid4()),
            user_name=username,
            flight=flight,
            error_string=getattr(flight, "error_string", "") or "",
            flight_color_hex=getattr(flight, "flight_color_hex", "") or "",
        )
        return self._sort_pending_flights([*pending_flights, pending])

    def pending_flights_for_user(
        self,
        auth_token: str,
        *,
        pending_flights: Sequence[LegacyPendingFlight] = (),
    ) -> list[LegacyPendingFlight]:
        username = self._require_authenticated_user(auth_token)
        return self._sort_pending_flights([flight for flight in pending_flights if flight.user_name == username])

    def update_pending_flight(
        self,
        auth_token: str,
        pending_flight: LegacyPendingFlight,
        *,
        pending_flights: Sequence[LegacyPendingFlight] = (),
    ) -> list[LegacyPendingFlight]:
        username = self._require_authenticated_user(auth_token)
        self._validate_pending_flight_owner(username, pending_flight, pending_flights)

        updated = [
            pending_flight if existing.pending_id == pending_flight.pending_id else existing
            for existing in pending_flights
        ]
        return self._sort_pending_flights(updated)

    def delete_pending_flight(
        self,
        auth_token: str,
        pending_id: str,
        *,
        pending_flights: Sequence[LegacyPendingFlight] = (),
    ) -> list[LegacyPendingFlight]:
        username = self._require_authenticated_user(auth_token)
        target = next((flight for flight in pending_flights if flight.pending_id == pending_id), None)
        if target is None or target.user_name != username:
            raise LegacyMobileCompatibilityError("Flight not owned by this user")

        return self._sort_pending_flights(
            [flight for flight in pending_flights if flight.pending_id != pending_id]
        )

    def commit_pending_flight(
        self,
        auth_token: str,
        pending_flight: LegacyPendingFlight,
        *,
        pending_flights: Sequence[LegacyPendingFlight] = (),
        existing_flights: Sequence[Flight] = (),
        committed_flights: list[Flight] | None = None,
    ) -> list[LegacyPendingFlight]:
        username = self._require_authenticated_user(auth_token)
        self._validate_pending_flight_owner(username, pending_flight, pending_flights)

        committed = self.commit_flight_with_options(
            auth_token,
            pending_flight.flight,
            existing_flights=existing_flights,
        )
        if committed_flights is not None:
            committed_flights.append(committed)

        return self.delete_pending_flight(
            auth_token,
            pending_flight.pending_id,
            pending_flights=pending_flights,
        )

    def sync_named_queries(self) -> LegacyNamedQueryContract:
        return LegacyNamedQueryContract(self._compatibility_service)

    def sync_legacy_property_contract(self) -> LegacyPropertyContract:
        return LegacyPropertyContract(self._compatibility_service)

    async def delete_legacy_image(
        self,
        auth_token: str,
        image_reference: LegacyMobileImageReference,
        *,
        session: AsyncSession,
        delete_storage_object: Callable[[str], Awaitable[None]] = delete_media_object,
    ) -> bool:
        if image_reference is None:
            raise TypeError("image_reference is required")
        if session is None:
            raise TypeError("session is required")

        username = self._require_authenticated_user(auth_token)
        canonical_user_id = await self._resolve_canonical_user_id(session, username)
        if canonical_user_id is None:
            raise LegacyMobileCompatibilityError("Authenticated legacy user is not mapped to a canonical user")

        mapping = await self._load_legacy_image_mapping(session, image_reference)
        if mapping is None:
            return False

        try:
            asset_id = UUID(mapping.canonical_entity_id)
        except (TypeError, ValueError):
            return False

        image_asset = await session.get(ImageAsset, asset_id)
        if image_asset is None:
            return False
        if str(image_asset.user_id) != canonical_user_id:
            raise LegacyMobileCompatibilityError("Image not owned by this user")

        for storage_key in self._image_storage_keys(image_asset):
            await delete_storage_object(storage_key)

        await session.delete(image_asset)
        await session.delete(mapping)
        await session.commit()
        return True

    def _decode_user_or_none(self, auth_token: str) -> str | None:
        username = self._compatibility_service.get_encrypted_user(auth_token)
        return username or None

    def _require_authenticated_user(self, auth_token: str) -> str:
        username = self._decode_user_or_none(auth_token)
        if username is None:
            raise LegacyMobileAuthenticationError("Bad auth")
        return username

    def _filter_flights(self, flights: Sequence[Flight], query: LegacyFlightQuery | None) -> list[Flight]:
        filtered = list(flights)
        if query is not None:
            if query.date_min is not None:
                min_date = self._coerce_date(query.date_min)
                filtered = [
                    flight for flight in filtered if self._coerce_date(getattr(flight, "flight_date", None)) >= min_date
                ]
            if query.date_max is not None:
                max_date = self._coerce_date(query.date_max)
                filtered = [
                    flight for flight in filtered if self._coerce_date(getattr(flight, "flight_date", None)) <= max_date
                ]
            if query.route_contains:
                route_contains = html.unescape(query.route_contains).strip().casefold()
                filtered = [
                    flight
                    for flight in filtered
                    if route_contains in ((getattr(flight, "route", "") or "").casefold())
                ]

        return sorted(
            filtered,
            key=lambda flight: (
                self._coerce_date(getattr(flight, "flight_date", None)),
                _normalize_optional_utc_datetime(getattr(flight, "created_at", None)) or _DOTNET_EPOCH,
            ),
            reverse=True,
        )

    @staticmethod
    def _coerce_date(value: date | datetime | None) -> date:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return date.min

    @staticmethod
    def _summary_to_legacy_items(summary) -> list[LegacyTotalsItem]:
        fields = [
            ("total_flight_time", "Total Flight Time"),
            ("pic_time", "PIC"),
            ("sic_time", "SIC"),
            ("dual_given", "Dual Given"),
            ("dual_received", "Dual Received"),
            ("cross_country", "Cross Country"),
            ("night", "Night"),
            ("imc", "IMC"),
            ("simulated_instrument", "Simulated Instrument"),
            ("landings", "Landings"),
            ("full_stop_landings_day", "Full Stop Day Landings"),
            ("full_stop_landings_night", "Full Stop Night Landings"),
            ("approaches", "Approaches"),
            ("flight_count", "Flight Count"),
        ]
        return [
            LegacyTotalsItem(key=key, label=label, value=getattr(summary, key))
            for key, label in fields
        ]

    @staticmethod
    def _flight_signature(flight: Flight) -> tuple[object, ...]:
        return (
            getattr(flight, "flight_date", None),
            str(getattr(flight, "aircraft_id", "")),
            getattr(flight, "route", "") or "",
            float(getattr(flight, "total_time", 0) or 0),
            float(getattr(flight, "pic_time", 0) or 0),
            float(getattr(flight, "sic_time", 0) or 0),
            getattr(flight, "remarks", "") or "",
            int(getattr(flight, "landings", 0) or 0),
            int(getattr(flight, "approaches", 0) or 0),
        )

    @staticmethod
    def _sort_pending_flights(pending_flights: Sequence[LegacyPendingFlight]) -> list[LegacyPendingFlight]:
        return sorted(
            pending_flights,
            key=lambda flight: (
                LegacyLogbookContract._coerce_date(getattr(flight.flight, "flight_date", None)),
                _normalize_optional_utc_datetime(getattr(flight.flight, "created_at", None)) or _DOTNET_EPOCH,
            ),
            reverse=True,
        )

    @staticmethod
    def _validate_pending_flight_owner(
        username: str,
        pending_flight: LegacyPendingFlight,
        pending_flights: Sequence[LegacyPendingFlight],
    ) -> None:
        if pending_flight.user_name != username:
            raise LegacyMobileCompatibilityError("Flight not owned by this user")
        if not any(
            existing.pending_id == pending_flight.pending_id and existing.user_name == username
            for existing in pending_flights
        ):
            raise LegacyMobileCompatibilityError("Flight not owned by this user")

    @staticmethod
    async def _resolve_canonical_user_id(session: AsyncSession, legacy_username: str) -> str | None:
        result = await session.execute(select(User.id).where(User.legacy_username == legacy_username))
        user_id = result.scalar_one_or_none()
        return None if user_id is None else str(user_id)

    @staticmethod
    async def _load_legacy_image_mapping(
        session: AsyncSession,
        image_reference: LegacyMobileImageReference,
    ) -> LegacyEntityMapping | None:
        legacy_identifier = image_reference.legacy_identifier.strip()
        if not legacy_identifier:
            raise LegacyMobileCompatibilityError("Legacy image identifier is required")

        result = await session.execute(
            select(LegacyEntityMapping).where(
                LegacyEntityMapping.legacy_system == image_reference.legacy_system,
                LegacyEntityMapping.legacy_table == image_reference.legacy_table,
                LegacyEntityMapping.legacy_identifier == legacy_identifier,
                LegacyEntityMapping.entity_type == _LEGACY_IMAGE_ENTITY_TYPE,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _image_storage_keys(image_asset: ImageAsset) -> list[str]:
        metadata = image_asset.metadata_json or {}
        keys = [image_asset.storage_key]
        for metadata_key in ("thumbnail_key", "web_key"):
            candidate = metadata.get(metadata_key)
            if isinstance(candidate, str) and candidate.strip():
                keys.append(candidate)
        return list(dict.fromkeys(keys))


@dataclass(frozen=True, slots=True)
class LegacyNamedQuery:
    query_name: str
    query: LegacyFlightQuery = field(default_factory=LegacyFlightQuery)
    color_string: str | None = None
    user_name: str | None = None

    @property
    def is_default(self) -> bool:
        return (
            self.query.date_min is None
            and self.query.date_max is None
            and not (self.query.route_contains or "").strip()
            and not (self.color_string or "").strip()
        )

    def to_legacy_payload(self) -> dict[str, object]:
        return {
            "QueryName": self.query_name,
            "UserName": self.user_name,
            "ColorString": self.color_string,
            "DateMin": self.query.date_min,
            "DateMax": self.query.date_max,
            "RouteContains": self.query.route_contains,
        }


@dataclass(frozen=True, slots=True)
class LegacyTemplatePropTypeBundle:
    user_properties: tuple[Mapping[str, object], ...] = ()
    user_templates: tuple[Mapping[str, object], ...] = ()

    def to_legacy_payload(self) -> dict[str, object]:
        return {
            "UserProperties": list(self.user_properties),
            "UserTemplates": list(self.user_templates),
        }


@dataclass(frozen=True, slots=True)
class LegacyPropertyType:
    prop_type_id: int
    title: str
    user_name: str | None = None
    sort_key: int = 0

    def to_legacy_payload(self) -> dict[str, object]:
        return {
            "PropTypeID": self.prop_type_id,
            "Title": self.title,
            "UserName": self.user_name,
            "SortKey": self.sort_key,
        }


@dataclass(frozen=True, slots=True)
class LegacyFlightProperty:
    prop_id: int
    prop_type_id: int
    title: str
    value: object | None = None

    def to_legacy_payload(self) -> dict[str, object]:
        return {
            "PropID": self.prop_id,
            "PropTypeID": self.prop_type_id,
            "Title": self.title,
            "Value": self.value,
        }


@dataclass(frozen=True, slots=True)
class LegacyMutableFlightRecord:
    flight_id: str
    user_name: str
    flight: Flight | None = None
    properties: tuple[LegacyFlightProperty, ...] = ()


@dataclass(frozen=True, slots=True)
class LegacyMobileImageReference:
    legacy_identifier: str
    legacy_system: str = _LEGACY_MOBILE_IMAGE_SYSTEM
    legacy_table: str = _LEGACY_MOBILE_IMAGE_TABLE


@dataclass(frozen=True, slots=True)
class LegacyPendingFlight:
    pending_id: str
    user_name: str
    flight: Flight
    error_string: str = ""
    flight_color_hex: str = ""

    def to_legacy_payload(self) -> dict[str, object]:
        return {
            "PendingID": self.pending_id,
            "UserName": self.user_name,
            "FlightDate": getattr(self.flight, "flight_date", None),
            "Route": getattr(self.flight, "route", ""),
            "ErrorString": self.error_string,
            "FlightColorHex": self.flight_color_hex,
        }


class LegacyNamedQueryContract:
    def __init__(self, compatibility_service: LegacyMobileCompatibilityService) -> None:
        self._compatibility_service = compatibility_service

    def get_named_queries_for_user(
        self,
        auth_token: str,
        queries: Sequence[LegacyNamedQuery],
    ) -> list[LegacyNamedQuery] | None:
        username = self._compatibility_service.get_encrypted_user(auth_token)
        if not username:
            return None

        normalized = [
            LegacyNamedQuery(
                query_name=query.query_name,
                query=query.query,
                color_string=query.color_string,
                user_name=username,
            )
            for query in queries
        ]
        return sorted(normalized, key=lambda item: item.query_name.casefold())

    def add_named_query_for_user(
        self,
        auth_token: str,
        query: LegacyFlightQuery,
        name: str,
        *,
        existing_queries: Sequence[LegacyNamedQuery] = (),
        color_string: str | None = None,
    ) -> list[LegacyNamedQuery] | None:
        if auth_token is None:
            raise TypeError("auth_token is required")
        if query is None:
            raise TypeError("query is required")
        if name is None:
            raise TypeError("name is required")
        if not name.strip():
            raise LegacyMobileCompatibilityError("Missing or empty name passed to AddNamedQueryForUser")

        username = self._compatibility_service.get_encrypted_user(auth_token)
        if not username:
            return None

        candidate = LegacyNamedQuery(
            query_name=name.strip(),
            query=query,
            color_string=color_string,
            user_name=username,
        )
        if candidate.is_default:
            return self.get_named_queries_for_user(auth_token, existing_queries)

        updated_queries: list[LegacyNamedQuery] = []
        preserved_color = color_string
        for existing in existing_queries:
            if existing.query_name.casefold() == candidate.query_name.casefold():
                if not preserved_color:
                    preserved_color = existing.color_string
                continue
            updated_queries.append(existing)

        updated_queries.append(
            LegacyNamedQuery(
                query_name=candidate.query_name,
                query=candidate.query,
                color_string=preserved_color,
                user_name=username,
            )
        )
        return self.get_named_queries_for_user(auth_token, updated_queries)

    def delete_named_query_for_user(
        self,
        auth_token: str,
        query_name: str,
        *,
        existing_queries: Sequence[LegacyNamedQuery] = (),
    ) -> list[LegacyNamedQuery] | None:
        if auth_token is None:
            raise TypeError("auth_token is required")
        if query_name is None:
            raise TypeError("query_name is required")

        username = self._compatibility_service.get_encrypted_user(auth_token)
        if not username:
            return None
        if not query_name.strip():
            raise LegacyMobileAuthenticationError("No query name specified")

        remaining = [
            query for query in existing_queries if query.query_name.casefold() != query_name.strip().casefold()
        ]
        return self.get_named_queries_for_user(auth_token, remaining)

    def properties_and_templates_for_user(
        self,
        auth_token: str,
        *,
        user_properties: Sequence[Mapping[str, object]] = (),
        user_templates: Sequence[Mapping[str, object]] = (),
    ) -> LegacyTemplatePropTypeBundle:
        username = self._compatibility_service.get_encrypted_user(auth_token)
        if not username:
            return LegacyTemplatePropTypeBundle()

        return LegacyTemplatePropTypeBundle(
            user_properties=tuple(user_properties),
            user_templates=tuple(user_templates),
        )


class LegacyPropertyContract:
    def __init__(self, compatibility_service: LegacyMobileCompatibilityService) -> None:
        self._compatibility_service = compatibility_service

    def available_property_types(
        self,
        property_types: Sequence[LegacyPropertyType],
    ) -> list[LegacyPropertyType]:
        return self._sorted_property_types(
            [item for item in property_types if not (item.user_name or "").strip()]
        )

    def available_property_types_for_user(
        self,
        auth_token: str,
        property_types: Sequence[LegacyPropertyType],
    ) -> list[LegacyPropertyType] | None:
        username = self._compatibility_service.get_encrypted_user(auth_token)
        if not username:
            return None

        return self._sorted_property_types(
            [
                item
                for item in property_types
                if not (item.user_name or "").strip() or item.user_name.casefold() == username.casefold()
            ]
        )

    def properties_for_flight(
        self,
        auth_token: str,
        flight_id: str,
        *,
        flights: Sequence[LegacyMutableFlightRecord] = (),
    ) -> list[LegacyFlightProperty] | None:
        username = self._compatibility_service.get_encrypted_user(auth_token)
        if not username:
            return None

        record = self._find_owned_flight_record(username, flight_id, flights)
        return None if record is None else list(record.properties)

    def delete_properties_for_flight(
        self,
        auth_token: str,
        flight_id: str,
        prop_ids: Sequence[int] | None,
        *,
        flights: Sequence[LegacyMutableFlightRecord] = (),
    ) -> list[LegacyMutableFlightRecord]:
        if prop_ids is None:
            return list(flights)

        username = self._require_authenticated_user(auth_token)
        property_ids = {int(prop_id) for prop_id in prop_ids}

        updated: list[LegacyMutableFlightRecord] = []
        for flight in flights:
            if not self._matches_owned_flight(username, flight, flight_id):
                updated.append(flight)
                continue

            updated.append(
                LegacyMutableFlightRecord(
                    flight_id=flight.flight_id,
                    user_name=flight.user_name,
                    flight=flight.flight,
                    properties=tuple(prop for prop in flight.properties if prop.prop_id not in property_ids),
                )
            )
        return updated

    def delete_property_for_flight(
        self,
        auth_token: str,
        flight_id: str,
        prop_id: int,
        *,
        flights: Sequence[LegacyMutableFlightRecord] = (),
    ) -> list[LegacyMutableFlightRecord]:
        return self.delete_properties_for_flight(
            auth_token,
            flight_id,
            [prop_id],
            flights=flights,
        )

    def delete_logbook_entry(
        self,
        auth_token: str,
        flight_id: str,
        *,
        flights: Sequence[LegacyMutableFlightRecord] = (),
    ) -> tuple[bool, list[LegacyMutableFlightRecord]]:
        username = self._require_authenticated_user(auth_token)
        if not str(flight_id or "").strip():
            raise LegacyMobileCompatibilityError("Invalid flight identifier")

        deleted = False
        remaining: list[LegacyMutableFlightRecord] = []
        for flight in flights:
            if self._matches_owned_flight(username, flight, flight_id):
                deleted = True
                continue
            remaining.append(flight)

        return deleted, remaining

    @staticmethod
    def _sorted_property_types(property_types: Sequence[LegacyPropertyType]) -> list[LegacyPropertyType]:
        return sorted(
            property_types,
            key=lambda item: (item.sort_key, item.title.casefold(), item.prop_type_id),
        )

    @staticmethod
    def _matches_owned_flight(username: str, flight: LegacyMutableFlightRecord, flight_id: str) -> bool:
        return flight.flight_id == flight_id and flight.user_name.casefold() == username.casefold()

    @classmethod
    def _find_owned_flight_record(
        cls,
        username: str,
        flight_id: str,
        flights: Sequence[LegacyMutableFlightRecord],
    ) -> LegacyMutableFlightRecord | None:
        return next((flight for flight in flights if cls._matches_owned_flight(username, flight, flight_id)), None)

    def _require_authenticated_user(self, auth_token: str) -> str:
        username = self._compatibility_service.get_encrypted_user(auth_token)
        if not username:
            raise LegacyMobileAuthenticationError("Bad auth")
        return username


class LegacyMobileAuthStore(Protocol):
    def get_user(self, username: str) -> LegacyMobileUserRecord | None:
        ...

    def find_username_by_email(self, email: str) -> str | None:
        ...

    def validate_credentials(self, username: str, password: str) -> str | None:
        ...


class LegacyMobileCompatibilityService:
    def __init__(
        self,
        *,
        auth_store: LegacyMobileAuthStore,
        authorized_clients: Collection[str] = (),
        token_signing_key: str | bytes = _DEFAULT_TOKEN_SIGNING_KEY,
        current_time: Callable[[], datetime] | None = None,
        two_factor_validator: Callable[[str, str], bool] | None = None,
    ) -> None:
        self.auth_store = auth_store
        self._authorized_clients = {client.casefold() for client in authorized_clients if client and client.strip()}
        self._token_signing_key = (
            token_signing_key.encode("utf-8")
            if isinstance(token_signing_key, str)
            else token_signing_key
        )
        self._current_time = current_time or (lambda: datetime.now(timezone.utc))
        self._two_factor_validator = two_factor_validator or self._default_two_factor_validator

    def is_authorized_service(self, app_token: str | None) -> bool:
        if app_token is None:
            return False
        normalized = app_token.strip()
        if not normalized:
            return False
        return normalized.casefold() in self._authorized_clients

    def issue_legacy_auth_token(
        self,
        app_token: str | None,
        username: str,
        password: str,
    ) -> str | None:
        issued = self._authenticate_and_issue_token(app_token=app_token, username=username, password=password)
        return None if issued is None else issued.auth_token

    def issue_legacy_auth_result(
        self,
        app_token: str | None,
        username: str,
        password: str,
        *,
        two_factor_code: str | None = None,
    ) -> LegacyAuthResult:
        issued = self._authenticate_and_issue_token(app_token=app_token, username=username, password=password)
        if issued is None:
            return LegacyAuthResult()

        second_factor_user = issued.authenticating_user
        if second_factor_user.two_factor_secret:
            if not two_factor_code:
                return LegacyAuthResult(result=LegacyAuthStatus.TwoFactorCodeRequired)
            if not self._two_factor_validator(second_factor_user.two_factor_secret, two_factor_code):
                raise LegacyMobileAuthenticationError("Two-factor authentication code failed")

        return LegacyAuthResult(result=LegacyAuthStatus.Success, auth_token=issued.auth_token)

    def refresh_legacy_auth_token(
        self,
        app_token: str | None,
        username: str,
        password: str,
        previous_token: str,
    ) -> str | None:
        if previous_token is None:
            raise TypeError("previous_token is required")

        try:
            previous_user = self.get_encrypted_user(previous_token)
            if not previous_user:
                return None
        except LegacyMobileAuthenticationError:
            return None

        new_token = self.issue_legacy_auth_token(app_token, username, password)
        if new_token is None:
            return None

        return new_token if self.get_encrypted_user(new_token) == previous_user else None

    def get_encrypted_user(self, auth_user_token: str) -> str:
        if auth_user_token is None or not auth_user_token:
            raise LegacyMobileAuthenticationError("Bad sign in")

        payload = self.decode_legacy_auth_token(auth_user_token)
        if payload is None:
            return ""

        user = self.auth_store.get_user(payload.username)
        if (
            user is not None
            and user.last_password_change is not None
            and self._normalize_datetime(user.last_password_change) > payload.issued_at
        ):
            raise LegacyMobileAuthenticationError("Authentication token expired after a password change")

        return payload.username

    def decode_legacy_auth_token(self, auth_user_token: str) -> LegacyAuthTokenPayload | None:
        parts = auth_user_token.split(".", 1)
        if len(parts) != 2:
            return None

        payload_bytes = self._urlsafe_b64decode(parts[0])
        signature_bytes = self._urlsafe_b64decode(parts[1])
        if payload_bytes is None or signature_bytes is None:
            return None

        expected_signature = hmac.new(self._token_signing_key, payload_bytes, hashlib.sha256).digest()
        if not hmac.compare_digest(signature_bytes, expected_signature):
            return None

        try:
            serialized_payload = payload_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return None

        username, separator, ticks_text = serialized_payload.partition(";")
        if separator != ";" or not username:
            return None

        try:
            issued_ticks = int(ticks_text)
        except ValueError:
            return None

        return LegacyAuthTokenPayload(
            username=username,
            issued_ticks=issued_ticks,
            issued_at=self._ticks_to_datetime(issued_ticks),
        )

    def _authenticate_and_issue_token(
        self,
        *,
        app_token: str | None,
        username: str,
        password: str,
    ) -> _IssuedLegacyAuthToken | None:
        if not self.is_authorized_service(app_token):
            return None
        if username is None:
            raise TypeError("username is required")
        if password is None:
            raise TypeError("password is required")

        emulated_username, login_name = self._split_emulation_request(username)
        resolved_login = self._resolve_login_name(login_name)
        if not resolved_login:
            return None

        authenticated_username = self._validate_credentials(resolved_login, password)
        if authenticated_username is None:
            return None

        authenticating_user = self.auth_store.get_user(authenticated_username)
        if authenticating_user is None:
            return None

        token_user = authenticating_user
        if emulated_username:
            if not (authenticating_user.can_support or authenticating_user.can_manage_data):
                raise LegacyMobileAuthorizationError("User is not authorized to emulate another account")

            emulated_user = self.auth_store.get_user(emulated_username)
            if emulated_user is None:
                raise LegacyMobileCompatibilityError(f"No such user: {emulated_username}")
            token_user = emulated_user

        return _IssuedLegacyAuthToken(
            auth_token=self._sign_token(token_user.username),
            token_user=token_user,
            authenticating_user=authenticating_user,
        )

    def _resolve_login_name(self, username: str) -> str:
        if "@" not in username:
            return username
        return self.auth_store.find_username_by_email(username) or ""

    def _split_emulation_request(self, username: str) -> tuple[str | None, str]:
        parts = [part for part in (username or "").split(":") if part]
        if len(parts) == 2:
            return parts[0], parts[1]
        return None, username

    def _validate_credentials(self, username: str, password: str) -> str | None:
        for candidate in self._password_candidates(password):
            validated_username = self.auth_store.validate_credentials(username, candidate)
            if validated_username:
                return validated_username
        return None

    def _password_candidates(self, password: str) -> tuple[str, ...]:
        unescaped = html.unescape(password)
        if unescaped == password:
            return (password,)
        return (password, unescaped)

    def _sign_token(self, username: str) -> str:
        issued_at = self._normalize_datetime(self._current_time())
        issued_ticks = self._datetime_to_ticks(issued_at)
        payload = f"{username};{issued_ticks}".encode("utf-8")
        signature = hmac.new(self._token_signing_key, payload, hashlib.sha256).digest()
        return f"{self._urlsafe_b64encode(payload)}.{self._urlsafe_b64encode(signature)}"

    @staticmethod
    def _default_two_factor_validator(secret: str, code: str) -> bool:
        return hmac.compare_digest((secret or "").strip(), (code or "").strip())

    @staticmethod
    def _datetime_to_ticks(value: datetime) -> int:
        normalized = LegacyMobileCompatibilityService._normalize_datetime(value)
        delta = normalized - _DOTNET_EPOCH
        return (
            ((delta.days * 24 * 60 * 60) + delta.seconds) * _DOTNET_TICKS_PER_SECOND
            + delta.microseconds * _DOTNET_TICKS_PER_MICROSECOND
        )

    @staticmethod
    def _ticks_to_datetime(ticks: int) -> datetime:
        seconds, remainder = divmod(ticks, _DOTNET_TICKS_PER_SECOND)
        microseconds = remainder // _DOTNET_TICKS_PER_MICROSECOND
        return _DOTNET_EPOCH + timedelta(seconds=seconds, microseconds=microseconds)

    @staticmethod
    def _normalize_datetime(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @staticmethod
    def _urlsafe_b64encode(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")

    @staticmethod
    def _urlsafe_b64decode(value: str) -> bytes | None:
        try:
            padding = "=" * (-len(value) % 4)
            return base64.urlsafe_b64decode(f"{value}{padding}".encode("ascii"))
        except (ValueError, UnicodeEncodeError):
            return None

    def sync_legacy_aircraft_contract(self) -> LegacyAircraftContract:
        return LegacyAircraftContract(self)

    def sync_legacy_logbook_contract(self) -> LegacyLogbookContract:
        return LegacyLogbookContract(self)
