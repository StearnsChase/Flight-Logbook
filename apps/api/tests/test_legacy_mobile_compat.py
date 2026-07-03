from __future__ import annotations

import json

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from myflightbook_api.models.aircraft import Aircraft
from myflightbook_api.models.category_class import CatClassID
from myflightbook_api.models.country_code import CountryCodePrefix, HyphenPreference
from myflightbook_api.models.deadline import Deadline, RegenUnit
from myflightbook_api.models.flight import Flight
from myflightbook_api.models.legacy import LegacyEntityMapping
from myflightbook_api.models.make_model import AllowedAircraftTypes, MakeModel, Manufacturer, TurbineLevel
from myflightbook_api.models.media import ImageAsset, MediaType
from myflightbook_api.services.currency import tracker as tracker_service
from myflightbook_api.services.currency.tracker import CurrencyState
from myflightbook_api.services.compat.legacy_mobile import (
    LegacyAircraftMaintenanceSnapshot,
    LegacyAircraftRecord,
    LegacyFlightProperty,
    LegacyFlightQuery,
    LegacyMobileImageReference,
    LegacyNamedQuery,
    LegacyPendingFlight,
    LegacyMobileAuthenticationError,
    LegacyMobileCompatibilityError,
    LegacyMobileCompatibilityService,
    LegacyMutableFlightRecord,
    LegacyPropertyType,
    LegacyMobileUserRecord,
)
from myflightbook_api.services.geography.latlong import LatLong


_FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "compat" / "legacy_mobile" / "auth"


@dataclass(slots=True)
class _StoredUser:
    record: LegacyMobileUserRecord
    password: str


class _MemoryAuthStore:
    def __init__(self, users: list[dict[str, object]]) -> None:
        self._users: dict[str, _StoredUser] = {}
        self._emails: dict[str, str] = {}

        for user in users:
            record = LegacyMobileUserRecord(
                username=str(user["username"]),
                email=str(user["email"]) if user.get("email") else None,
                last_password_change=_parse_datetime(user.get("last_password_change")),
                can_support=bool(user.get("can_support", False)),
                can_manage_data=bool(user.get("can_manage_data", False)),
                two_factor_secret=str(user["two_factor_secret"]) if user.get("two_factor_secret") else None,
            )
            self.replace_user(record, password=str(user["password"]))

    def get_user(self, username: str) -> LegacyMobileUserRecord | None:
        stored = self._users.get(username.casefold())
        return None if stored is None else stored.record

    def find_username_by_email(self, email: str) -> str | None:
        return self._emails.get(email.casefold())

    def validate_credentials(self, username: str, password: str) -> str | None:
        stored = self._users.get(username.casefold())
        if stored is None or stored.password != password:
            return None
        return stored.record.username

    def replace_user(self, record: LegacyMobileUserRecord, *, password: str) -> None:
        self._users[record.username.casefold()] = _StoredUser(record=record, password=password)
        if record.email:
            self._emails[record.email.casefold()] = record.username


class _FakeScalarResult:
    def __init__(self, values):
        self._values = values

    def all(self):
        if isinstance(self._values, list):
            return list(self._values)
        if self._values is None:
            return []
        return [self._values]

    def first(self):
        values = self.all()
        return values[0] if values else None


class _FakeExecuteResult:
    def __init__(self, value):
        self._value = value

    def scalars(self):
        return _FakeScalarResult(self._value)

    def scalar_one_or_none(self):
        values = self.scalars().all()
        if len(values) > 1:
            raise AssertionError("Expected one or zero values")
        return values[0] if values else None


class _FakeSession:
    def __init__(self, results: list[object], *, get_results: dict[tuple[type, object], object] | None = None) -> None:
        self._results = iter(results)
        self._get_results = get_results or {}
        self.statements = []
        self.added = []
        self.deleted = []
        self.commit_count = 0

    async def execute(self, statement):
        self.statements.append(statement)
        return _FakeExecuteResult(next(self._results))

    async def get(self, model, key):
        return self._get_results.get((model, key))

    async def delete(self, item) -> None:
        self.deleted.append(item)

    async def commit(self) -> None:
        self.commit_count += 1

    def add(self, item) -> None:
        self.added.append(item)


def _parse_datetime(value: object) -> datetime | None:
    if value is None:
        return None

    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _load_fixture(name: str) -> dict[str, object]:
    return json.loads((_FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def _service_from_fixture(name: str) -> tuple[_MemoryAuthStore, LegacyMobileCompatibilityService]:
    payload = _load_fixture(name)
    store = _MemoryAuthStore(payload["users"])
    current_time = _parse_datetime(payload["current_time"])

    service = LegacyMobileCompatibilityService(
        auth_store=store,
        authorized_clients=payload["authorized_clients"],
        token_signing_key="fixture-signing-key",
        current_time=lambda: current_time,
        two_factor_validator=lambda secret, code: secret == code,
    )
    return store, service


def _service_with_user(*users: dict[str, object], current_time: datetime | None = None) -> tuple[_MemoryAuthStore, LegacyMobileCompatibilityService]:
    store = _MemoryAuthStore(list(users))
    service = LegacyMobileCompatibilityService(
        auth_store=store,
        authorized_clients=["ios-client"],
        token_signing_key="fixture-signing-key",
        current_time=lambda: current_time or datetime(2026, 4, 20, 12, 0, tzinfo=timezone.utc),
        two_factor_validator=lambda secret, code: secret == code,
    )
    return store, service


def _issue_token(service: LegacyMobileCompatibilityService, username: str = "pilot", password: str = "secret-pass") -> str:
    token = service.issue_legacy_auth_token("ios-client", username, password)
    assert token is not None
    return token


def _country_codes() -> list[CountryCodePrefix]:
    return [
        CountryCodePrefix(country_name="United States", prefix="N", hyphen_pref=HyphenPreference.NO_HYPHEN),
        CountryCodePrefix(country_name="Canada", prefix="C", hyphen_pref=HyphenPreference.HYPHENATE),
    ]


def _make_model(*, allowed_types: AllowedAircraftTypes = AllowedAircraftTypes.ANY) -> MakeModel:
    return MakeModel(
        id=7,
        manufacturer_id=11,
        category_class_id=CatClassID.ASEL,
        model="172S",
        model_name="Skyhawk",
        type_name="",
        family_name="",
        army_mds="",
        allowed_types=allowed_types,
        engine_type=TurbineLevel.PISTON,
        is_complex=False,
        is_high_perf=False,
        is_200hp=True,
        is_tailwheel=False,
        is_constant_prop=False,
        has_flaps=True,
        is_retract=False,
        is_all_glass=False,
        is_all_taa=False,
        is_motor_glider=False,
        is_multi_helicopter=False,
        is_certified_single_pilot=True,
    )


def _flight_record(
    *,
    flight_date: date,
    route: str = "KAPA-KBJC",
    total_time: float = 1.5,
    approaches: int = 0,
    night_landings: int = 0,
    remarks: str | None = None,
    created_at: datetime | None = None,
) -> Flight:
    flight = Flight(
        user_id=str(uuid4()),
        aircraft_id=str(uuid4()),
        flight_date=flight_date,
        route=route,
        total_time=total_time,
        pic_time=total_time,
        cross_country=0.5,
        night=0.5 if night_landings else 0.0,
        full_stop_landings_night=night_landings,
        approaches=approaches,
        remarks=remarks,
    )
    timestamp = created_at or datetime(2026, 4, 20, 12, 0, tzinfo=timezone.utc)
    flight.created_at = timestamp
    flight.updated_at = timestamp
    return flight


@pytest.mark.parametrize(
    "fixture_name",
    [
        "auth_result_success_email_and_html_password.json",
        "auth_result_two_factor_required.json",
        "auth_result_support_emulation.json",
    ],
)
def test_issue_legacy_auth_result_matches_golden_fixtures(fixture_name: str) -> None:
    payload = _load_fixture(fixture_name)
    _, service = _service_from_fixture(fixture_name)
    request = payload["request"]
    expected = payload["expected"]

    result = service.issue_legacy_auth_result(
        request["app_token"],
        request["username"],
        request["password"],
        two_factor_code=request.get("two_factor_code"),
    )

    assert result.to_legacy_payload()["Result"] == expected["result"]
    if expected["auth_token_present"]:
        assert result.auth_token is not None
        assert service.get_encrypted_user(result.auth_token) == expected["decoded_user"]
    else:
        assert result.auth_token is None


def test_issue_legacy_auth_result_rejects_an_invalid_two_factor_code() -> None:
    store = _MemoryAuthStore(
        [
            {
                "username": "pilot",
                "email": "pilot@example.com",
                "password": "secret-pass",
                "two_factor_secret": "246810",
            }
        ]
    )
    service = LegacyMobileCompatibilityService(
        auth_store=store,
        authorized_clients=["ios-client"],
        token_signing_key="fixture-signing-key",
        current_time=lambda: datetime(2026, 4, 20, 12, 0, tzinfo=timezone.utc),
        two_factor_validator=lambda secret, code: secret == code,
    )

    with pytest.raises(LegacyMobileAuthenticationError, match="Two-factor"):
        service.issue_legacy_auth_result(
            "ios-client",
            "pilot",
            "secret-pass",
            two_factor_code="999999",
        )


def test_get_encrypted_user_returns_empty_string_for_a_malformed_token() -> None:
    store = _MemoryAuthStore([])
    service = LegacyMobileCompatibilityService(
        auth_store=store,
        authorized_clients=["ios-client"],
        token_signing_key="fixture-signing-key",
    )

    assert service.get_encrypted_user("bogus-token") == ""


def test_get_encrypted_user_rejects_tokens_issued_before_a_password_change() -> None:
    issued_at = datetime(2026, 4, 20, 12, 0, tzinfo=timezone.utc)
    store = _MemoryAuthStore(
        [
            {
                "username": "pilot",
                "email": "pilot@example.com",
                "password": "secret-pass",
                "last_password_change": "2026-04-01T08:30:00Z",
            }
        ]
    )
    service = LegacyMobileCompatibilityService(
        auth_store=store,
        authorized_clients=["ios-client"],
        token_signing_key="fixture-signing-key",
        current_time=lambda: issued_at,
    )

    auth_token = service.issue_legacy_auth_token("ios-client", "pilot", "secret-pass")
    assert auth_token is not None

    store.replace_user(
        LegacyMobileUserRecord(
            username="pilot",
            email="pilot@example.com",
            last_password_change=issued_at + timedelta(minutes=1),
        ),
        password="secret-pass",
    )

    with pytest.raises(LegacyMobileAuthenticationError, match="password change"):
        service.get_encrypted_user(auth_token)


def test_refresh_legacy_auth_token_reissues_a_token_for_the_same_user() -> None:
    timestamps = iter(
        [
            datetime(2026, 4, 20, 12, 0, tzinfo=timezone.utc),
            datetime(2026, 4, 20, 12, 5, tzinfo=timezone.utc),
        ]
    )
    store = _MemoryAuthStore(
        [
            {
                "username": "pilot",
                "email": "pilot@example.com",
                "password": "secret-pass",
            }
        ]
    )
    service = LegacyMobileCompatibilityService(
        auth_store=store,
        authorized_clients=["ios-client"],
        token_signing_key="fixture-signing-key",
        current_time=lambda: next(timestamps),
    )

    previous_token = service.issue_legacy_auth_token("ios-client", "pilot", "secret-pass")
    assert previous_token is not None

    refreshed_token = service.refresh_legacy_auth_token(
        "ios-client",
        "pilot",
        "secret-pass",
        previous_token,
    )

    assert refreshed_token is not None
    assert refreshed_token != previous_token
    assert service.get_encrypted_user(refreshed_token) == "pilot"


def test_refresh_legacy_auth_token_rejects_a_user_switch() -> None:
    timestamps = iter(
        [
            datetime(2026, 4, 20, 12, 0, tzinfo=timezone.utc),
            datetime(2026, 4, 20, 12, 5, tzinfo=timezone.utc),
        ]
    )
    store = _MemoryAuthStore(
        [
            {
                "username": "pilot",
                "email": "pilot@example.com",
                "password": "secret-pass",
            },
            {
                "username": "student",
                "email": "student@example.com",
                "password": "student-pass",
            },
        ]
    )
    service = LegacyMobileCompatibilityService(
        auth_store=store,
        authorized_clients=["ios-client"],
        token_signing_key="fixture-signing-key",
        current_time=lambda: next(timestamps),
    )

    previous_token = service.issue_legacy_auth_token("ios-client", "pilot", "secret-pass")
    assert previous_token is not None

    refreshed_token = service.refresh_legacy_auth_token(
        "ios-client",
        "student",
        "student-pass",
        previous_token,
    )

    assert refreshed_token is None


def test_sync_legacy_aircraft_contract_formats_anonymous_aircraft_and_normalizes_timestamps() -> None:
    _, service = _service_with_user(
        {
            "username": "pilot",
            "email": "pilot@example.com",
            "password": "secret-pass",
        }
    )
    auth_token = _issue_token(service)
    contract = service.sync_legacy_aircraft_contract()

    aircraft = Aircraft(owner_user_id=str(uuid4()), tail_number="N12345", display_name="Skyhawk")
    aircraft.id = uuid4()
    maintenance = LegacyAircraftMaintenanceSnapshot(
        last_altimeter=datetime(2026, 4, 20, 12, 0, 0),
        last_vor=datetime(1, 1, 1, 0, 0, 0),
    )

    result = contract.aircraft_for_user(
        auth_token,
        [aircraft],
        anonymous_tail_overrides={str(aircraft.id): "#C172"},
        maintenance_overrides={str(aircraft.id): maintenance},
    )

    assert result is not None
    assert result[0].tail_number == "#C172"
    assert result[0].is_anonymous is True
    assert result[0].maintenance.last_altimeter == datetime(2026, 4, 20, 12, 0, 0, tzinfo=timezone.utc)
    assert result[0].maintenance.last_vor is None


def test_legacy_aircraft_matching_prefix_uses_normalized_tails() -> None:
    _, service = _service_with_user(
        {
            "username": "pilot",
            "email": "pilot@example.com",
            "password": "secret-pass",
        }
    )
    auth_token = _issue_token(service)
    contract = service.sync_legacy_aircraft_contract()

    canadian = Aircraft(owner_user_id=str(uuid4()), tail_number="C-FABC", display_name="Canadian")
    canadian.id = uuid4()
    american = Aircraft(owner_user_id=str(uuid4()), tail_number="N12345", display_name="American")
    american.id = uuid4()

    matches = contract.aircraft_matching_prefix(auth_token, "cfab", [canadian, american])

    assert [item.tail_number for item in matches] == ["C-FABC"]


@pytest.mark.asyncio
async def test_add_legacy_aircraft_for_user_supports_anonymous_tail_resolution() -> None:
    _, service = _service_with_user(
        {
            "username": "pilot",
            "email": "pilot@example.com",
            "password": "secret-pass",
        }
    )
    auth_token = _issue_token(service)
    contract = service.sync_legacy_aircraft_contract()
    session = _FakeSession([[]])
    manufacturer = Manufacturer(id=11, name="Cessna")

    result = await contract.add_aircraft_for_user(
        auth_token,
        owner_user_id=str(uuid4()),
        tail_number="#C172",
        model_id=7,
        instance_type_id=1,
        session=session,
        make_model=_make_model(),
        manufacturer=manufacturer,
        country_codes=_country_codes(),
        anonymous_tail_resolver=lambda model_id: f"N{model_id}XX",
    )

    assert len(result) == 1
    assert result[0].tail_number == "N7XX"
    assert result[0].model_name == 'Cessna 172S "Skyhawk"'
    assert session.added[0].tail_number == "N7XX"


def test_update_maintenance_for_aircraft_normalizes_the_legacy_timestamp_payload() -> None:
    _, service = _service_with_user(
        {
            "username": "pilot",
            "email": "pilot@example.com",
            "password": "secret-pass",
        }
    )
    auth_token = _issue_token(service)
    contract = service.sync_legacy_aircraft_contract()
    aircraft = Aircraft(owner_user_id=str(uuid4()), tail_number="N12345", display_name="Skyhawk")
    aircraft.id = uuid4()
    aircraft.revision = 3
    record = LegacyAircraftRecord(
        aircraft_id="42",
        tail_number="N12345",
        display_name="Skyhawk",
        maintenance=LegacyAircraftMaintenanceSnapshot(
            last_transponder=datetime(2026, 4, 20, 12, 0, 0),
            registration_due=datetime(1, 1, 1, 0, 0, 0),
        ),
        public_notes="Shared",
        private_notes="Owner only",
        user_flags=7,
        revision=3,
    )

    updated = contract.update_maintenance_for_aircraft(
        auth_token,
        aircraft,
        record,
        update_flags=True,
        update_notes=True,
    )

    assert updated.maintenance.last_transponder == datetime(2026, 4, 20, 12, 0, 0, tzinfo=timezone.utc)
    assert updated.maintenance.registration_due is None
    assert updated.public_notes == "Shared"
    assert updated.private_notes == "Owner only"
    assert updated.user_flags == 7
    assert updated.revision == 4
    assert aircraft.public_notes == "Shared"
    assert aircraft.private_notes == "Owner only"
    assert aircraft.user_flags == 7


def test_update_maintenance_for_aircraft_rejects_stale_revisions() -> None:
    _, service = _service_with_user(
        {
            "username": "pilot",
            "email": "pilot@example.com",
            "password": "secret-pass",
        }
    )
    auth_token = _issue_token(service)
    contract = service.sync_legacy_aircraft_contract()
    aircraft = Aircraft(owner_user_id=str(uuid4()), tail_number="N12345", display_name="Skyhawk")
    aircraft.id = uuid4()
    aircraft.revision = 2
    payload = LegacyAircraftRecord(aircraft_id=str(aircraft.id), tail_number="N12345", display_name="Skyhawk", revision=1)

    with pytest.raises(LegacyMobileCompatibilityError, match="most recent revision"):
        contract.update_maintenance_for_aircraft(auth_token, aircraft, payload)


def test_delete_legacy_aircraft_for_user_filters_the_removed_aircraft() -> None:
    _, service = _service_with_user(
        {
            "username": "pilot",
            "email": "pilot@example.com",
            "password": "secret-pass",
        }
    )
    auth_token = _issue_token(service)
    contract = service.sync_legacy_aircraft_contract()

    first = Aircraft(owner_user_id=str(uuid4()), tail_number="N12345", display_name="First")
    first.id = uuid4()
    second = Aircraft(owner_user_id=str(uuid4()), tail_number="N67890", display_name="Second")
    second.id = uuid4()

    remaining = contract.delete_aircraft_for_user(auth_token, str(first.id), [first, second])

    assert [item.tail_number for item in remaining] == ["N67890"]


def test_sync_legacy_logbook_contract_returns_currency_items_for_flights_and_deadlines(monkeypatch: pytest.MonkeyPatch) -> None:
    now = datetime(2026, 4, 20, 12, 0, 0)
    monkeypatch.setattr(tracker_service, "_current_time", lambda: now)
    _, service = _service_with_user(
        {
            "username": "pilot",
            "email": "pilot@example.com",
            "password": "secret-pass",
        }
    )
    auth_token = _issue_token(service)
    contract = service.sync_legacy_logbook_contract()
    deadline = Deadline(name="Flight Review", regen_type=RegenUnit.DAYS, regen_span=90)
    deadline.expiration = now + timedelta(days=10)

    statuses = contract.get_currency_for_user(
        auth_token,
        [_flight_record(flight_date=date(2026, 4, 19), approaches=6, night_landings=3, remarks="ILS practice and hold")],
        deadlines=[deadline],
    )

    assert statuses is not None
    assert [item.label for item in statuses] == ["Night Currency", "IFR Currency", "Flight Review"]
    assert statuses[0].state == CurrencyState.OK
    assert statuses[1].state == CurrencyState.OK
    assert statuses[2].state == CurrencyState.GETTING_CLOSE


def test_legacy_logbook_totals_for_user_filters_by_minimum_date() -> None:
    _, service = _service_with_user(
        {
            "username": "pilot",
            "email": "pilot@example.com",
            "password": "secret-pass",
        }
    )
    auth_token = _issue_token(service)
    contract = service.sync_legacy_logbook_contract()

    items = contract.totals_for_user(
        auth_token,
        [
            _flight_record(flight_date=date(2026, 3, 20), total_time=2.0),
            _flight_record(flight_date=date(2026, 4, 20), total_time=1.5, approaches=2),
        ],
        datetime(2026, 4, 1, 0, 0, tzinfo=timezone.utc),
    )

    totals = {item.key: item.value for item in items or []}
    assert totals["flight_count"] == 1
    assert totals["total_flight_time"] == 1.5
    assert totals["approaches"] == 2


def test_legacy_logbook_visited_airports_counts_route_codes() -> None:
    _, service = _service_with_user(
        {
            "username": "pilot",
            "email": "pilot@example.com",
            "password": "secret-pass",
        }
    )
    auth_token = _issue_token(service)
    contract = service.sync_legacy_logbook_contract()

    visited = contract.visited_airports(
        auth_token,
        [
            _flight_record(flight_date=date(2026, 4, 20), route="KAPA KBJC"),
            _flight_record(flight_date=date(2026, 4, 21), route="KBJC KAPA KAPA"),
        ],
    )

    assert [airport.to_legacy_payload() for airport in visited or []] == [
        {"Code": "KAPA", "Visits": 3},
        {"Code": "KBJC", "Visits": 2},
    ]


def test_legacy_logbook_flights_with_query_applies_filters_and_pagination() -> None:
    _, service = _service_with_user(
        {
            "username": "pilot",
            "email": "pilot@example.com",
            "password": "secret-pass",
        }
    )
    auth_token = _issue_token(service)
    contract = service.sync_legacy_logbook_contract()
    flights = [
        _flight_record(
            flight_date=date(2026, 4, 22),
            route="KAPA-KBJC",
            created_at=datetime(2026, 4, 22, 12, 0, tzinfo=timezone.utc),
        ),
        _flight_record(
            flight_date=date(2026, 4, 21),
            route="KAPA-KDEN",
            created_at=datetime(2026, 4, 21, 12, 0, tzinfo=timezone.utc),
        ),
        _flight_record(
            flight_date=date(2026, 3, 20),
            route="KBJC-KPUB",
            created_at=datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc),
        ),
    ]

    filtered = contract.flights_with_query(
        auth_token,
        flights,
        query=LegacyFlightQuery(date_min=date(2026, 4, 1), route_contains="KAPA"),
        offset=1,
        max_count=1,
    )

    assert [flight.route for flight in filtered] == ["KAPA-KDEN"]


def test_legacy_logbook_check_flight_returns_lint_issue_descriptions() -> None:
    _, service = _service_with_user(
        {
            "username": "pilot",
            "email": "pilot@example.com",
            "password": "secret-pass",
        }
    )
    auth_token = _issue_token(service)
    contract = service.sync_legacy_logbook_contract()

    issues = contract.check_flight(auth_token, _flight_record(flight_date=date(2026, 4, 20)))

    assert "Aircraft is not loaded for this flight" in issues


def test_legacy_logbook_flight_path_gpx_serializes_points() -> None:
    _, service = _service_with_user(
        {
            "username": "pilot",
            "email": "pilot@example.com",
            "password": "secret-pass",
        }
    )
    auth_token = _issue_token(service)
    contract = service.sync_legacy_logbook_contract()
    flight_id = "flight-123"
    points = [LatLong(39.5, -104.8), LatLong(39.6, -104.7)]

    path = contract.flight_path_for_flight(auth_token, flight_id, flight_paths={flight_id: points})
    gpx = contract.flight_path_for_flight_gpx(auth_token, flight_id, flight_paths={flight_id: points})

    assert path is not None
    assert len(path) == 2
    assert gpx is not None
    assert '<trkpt lat="39.50000000" lon="-104.80000000"></trkpt>' in gpx
    assert "<name>flight-123</name>" in gpx


def test_named_query_contract_replaces_queries_and_preserves_color() -> None:
    _, service = _service_with_user(
        {
            "username": "pilot",
            "email": "pilot@example.com",
            "password": "secret-pass",
        }
    )
    auth_token = _issue_token(service)
    manager = service.sync_legacy_logbook_contract().sync_named_queries()
    existing = [
        LegacyNamedQuery(
            query_name="Recent KAPA",
            query=LegacyFlightQuery(route_contains="KAPA"),
            color_string="#ff0000",
            user_name="pilot",
        )
    ]

    updated = manager.add_named_query_for_user(
        auth_token,
        LegacyFlightQuery(route_contains="KBJC"),
        "Recent KAPA",
        existing_queries=existing,
    )
    deleted = manager.delete_named_query_for_user(
        auth_token,
        "Recent KAPA",
        existing_queries=updated or [],
    )

    assert updated is not None
    assert [query.to_legacy_payload() for query in updated] == [
        {
            "QueryName": "Recent KAPA",
            "UserName": "pilot",
            "ColorString": "#ff0000",
            "DateMin": None,
            "DateMax": None,
            "RouteContains": "KBJC",
        }
    ]
    assert deleted == []


def test_named_query_contract_returns_property_template_bundle() -> None:
    _, service = _service_with_user(
        {
            "username": "pilot",
            "email": "pilot@example.com",
            "password": "secret-pass",
        }
    )
    auth_token = _issue_token(service)
    manager = service.sync_legacy_logbook_contract().sync_named_queries()

    bundle = manager.properties_and_templates_for_user(
        auth_token,
        user_properties=[{"Name": "Approaches"}],
        user_templates=[{"Name": "IFR Template"}],
    )

    assert bundle.to_legacy_payload() == {
        "UserProperties": [{"Name": "Approaches"}],
        "UserTemplates": [{"Name": "IFR Template"}],
    }


def test_property_contract_filters_types_and_mutates_legacy_flights() -> None:
    _, service = _service_with_user(
        {
            "username": "pilot",
            "email": "pilot@example.com",
            "password": "secret-pass",
        }
    )
    auth_token = _issue_token(service)
    contract = service.sync_legacy_logbook_contract().sync_legacy_property_contract()
    property_types = [
        LegacyPropertyType(prop_type_id=10, title="Approach", sort_key=1),
        LegacyPropertyType(prop_type_id=20, title="Personal Note", user_name="pilot", sort_key=2),
        LegacyPropertyType(prop_type_id=30, title="Other User", user_name="student", sort_key=3),
    ]
    flights = [
        LegacyMutableFlightRecord(
            flight_id="flight-1",
            user_name="pilot",
            properties=(
                LegacyFlightProperty(prop_id=101, prop_type_id=10, title="Approach", value="ILS"),
                LegacyFlightProperty(prop_id=202, prop_type_id=20, title="Personal Note", value="Night cross-country"),
            ),
        ),
        LegacyMutableFlightRecord(flight_id="flight-2", user_name="student"),
    ]

    anonymous_types = contract.available_property_types(property_types)
    user_types = contract.available_property_types_for_user(auth_token, property_types)
    properties = contract.properties_for_flight(auth_token, "flight-1", flights=flights)
    updated_flights = contract.delete_property_for_flight(auth_token, "flight-1", 101, flights=flights)
    deleted, remaining_flights = contract.delete_logbook_entry(auth_token, "flight-1", flights=updated_flights)

    assert [item.title for item in anonymous_types] == ["Approach"]
    assert [item.title for item in user_types or []] == ["Approach", "Personal Note"]
    assert [item.to_legacy_payload() for item in properties or []] == [
        {"PropID": 101, "PropTypeID": 10, "Title": "Approach", "Value": "ILS"},
        {"PropID": 202, "PropTypeID": 20, "Title": "Personal Note", "Value": "Night cross-country"},
    ]
    assert [item.prop_id for item in updated_flights[0].properties] == [202]
    assert deleted is True
    assert [flight.flight_id for flight in remaining_flights] == ["flight-2"]


@pytest.mark.asyncio
async def test_delete_legacy_image_deletes_the_owned_asset_and_mapping() -> None:
    _, service = _service_with_user(
        {
            "username": "pilot",
            "email": "pilot@example.com",
            "password": "secret-pass",
        }
    )
    auth_token = _issue_token(service)
    contract = service.sync_legacy_logbook_contract()
    user_id = str(uuid4())
    asset_id = uuid4()
    asset = ImageAsset(
        id=asset_id,
        user_id=user_id,
        flight_id=None,
        storage_key=f"images/{user_id}/{asset_id}/web.jpg",
        original_filename="panel.jpg",
        media_type=MediaType.IMAGE,
        metadata_json={
            "thumbnail_key": f"images/{user_id}/{asset_id}/thumb.jpg",
            "web_key": f"images/{user_id}/{asset_id}/web.jpg",
        },
    )
    mapping = LegacyEntityMapping(
        legacy_system="myflightbook-mobile",
        legacy_table="MFBImageInfo",
        legacy_identifier="legacy-thumb://asset-1",
        entity_type="image_asset",
        canonical_entity_id=str(asset_id),
    )
    session = _FakeSession(
        [user_id, mapping],
        get_results={(ImageAsset, asset_id): asset},
    )
    deleted_keys: list[str] = []

    async def fake_delete_object(key: str) -> None:
        deleted_keys.append(key)

    deleted = await contract.delete_legacy_image(
        auth_token,
        LegacyMobileImageReference("legacy-thumb://asset-1"),
        session=session,
        delete_storage_object=fake_delete_object,
    )

    assert deleted is True
    assert deleted_keys == [
        f"images/{user_id}/{asset_id}/web.jpg",
        f"images/{user_id}/{asset_id}/thumb.jpg",
    ]
    assert session.deleted == [asset, mapping]
    assert session.commit_count == 1


@pytest.mark.asyncio
async def test_delete_legacy_image_rejects_an_unowned_asset() -> None:
    _, service = _service_with_user(
        {
            "username": "pilot",
            "email": "pilot@example.com",
            "password": "secret-pass",
        }
    )
    auth_token = _issue_token(service)
    contract = service.sync_legacy_logbook_contract()
    asset_id = uuid4()
    asset = ImageAsset(
        id=asset_id,
        user_id=str(uuid4()),
        flight_id=None,
        storage_key=f"images/{asset_id}/web.jpg",
        original_filename="panel.jpg",
        media_type=MediaType.IMAGE,
        metadata_json=None,
    )
    mapping = LegacyEntityMapping(
        legacy_system="myflightbook-mobile",
        legacy_table="MFBImageInfo",
        legacy_identifier="legacy-thumb://asset-2",
        entity_type="image_asset",
        canonical_entity_id=str(asset_id),
    )
    session = _FakeSession(
        [str(uuid4()), mapping],
        get_results={(ImageAsset, asset_id): asset},
    )

    with pytest.raises(LegacyMobileCompatibilityError, match="owned by this user"):
        await contract.delete_legacy_image(
            auth_token,
            LegacyMobileImageReference("legacy-thumb://asset-2"),
            session=session,
            delete_storage_object=lambda key: None,  # pragma: no cover - should never be called
        )

    assert session.deleted == []
    assert session.commit_count == 0


def test_logbook_commit_flight_with_options_returns_an_existing_duplicate() -> None:
    _, service = _service_with_user(
        {
            "username": "pilot",
            "email": "pilot@example.com",
            "password": "secret-pass",
        }
    )
    auth_token = _issue_token(service)
    contract = service.sync_legacy_logbook_contract()
    aircraft_id = str(uuid4())
    existing = _flight_record(flight_date=date(2026, 4, 20), route="KAPA-KBJC", total_time=1.2, approaches=1)
    existing.id = uuid4()
    existing.aircraft_id = aircraft_id
    candidate = _flight_record(flight_date=date(2026, 4, 20), route="KAPA-KBJC", total_time=1.2, approaches=1)
    candidate.aircraft_id = aircraft_id

    committed = contract.commit_flight_with_options(auth_token, candidate, existing_flights=[existing])

    assert committed is existing


def test_pending_flight_lifecycle_updates_commits_and_clears_pending() -> None:
    _, service = _service_with_user(
        {
            "username": "pilot",
            "email": "pilot@example.com",
            "password": "secret-pass",
        }
    )
    auth_token = _issue_token(service)
    contract = service.sync_legacy_logbook_contract()
    initial_flight = _flight_record(flight_date=date(2026, 4, 20), route="KAPA-KBJC")

    pending = contract.create_pending_flight(auth_token, initial_flight)
    updated_pending = LegacyPendingFlight(
        pending_id=pending[0].pending_id,
        user_name=pending[0].user_name,
        flight=_flight_record(flight_date=date(2026, 4, 21), route="KAPA-KDEN"),
    )
    pending_after_update = contract.update_pending_flight(
        auth_token,
        updated_pending,
        pending_flights=pending,
    )
    committed_flights: list[Flight] = []

    remaining = contract.commit_pending_flight(
        auth_token,
        pending_after_update[0],
        pending_flights=pending_after_update,
        committed_flights=committed_flights,
    )

    assert [flight.flight.route for flight in pending_after_update] == ["KAPA-KDEN"]
    assert remaining == []
    assert len(committed_flights) == 1
    assert committed_flights[0].route == "KAPA-KDEN"
