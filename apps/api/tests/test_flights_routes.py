from __future__ import annotations

from datetime import date, datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from fastapi import HTTPException

from myflightbook_api.api.routes.flights import create_flight, get_flight, list_flights
from myflightbook_api.schemas.flight import FlightCreate


class _FakeScalarResult:
    def __init__(self, values):
        self._values = values

    def all(self):
        return list(self._values)


class _FakeExecuteResult:
    def __init__(self, value) -> None:
        self._value = value

    def scalars(self):
        return _FakeScalarResult(self._value)

    def scalar_one_or_none(self):
        return self._value


class _FakeSession:
    def __init__(self, results: list[object]) -> None:
        self._results = iter(results)
        self.statements = []
        self.added = []
        self.committed = False
        self.refreshed = []

    async def execute(self, statement):
        self.statements.append(statement)
        return _FakeExecuteResult(next(self._results))

    def add(self, item) -> None:
        self.added.append(item)

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, item) -> None:
        now = datetime.now(timezone.utc)
        if getattr(item, "id", None) is None:
            item.id = uuid4()
        if getattr(item, "created_at", None) is None:
            item.created_at = now
        if getattr(item, "updated_at", None) is None:
            item.updated_at = now
        self.refreshed.append(item)


def _flight_stub():
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=uuid4(),
        aircraft_id=uuid4(),
        flight_date=date(2026, 4, 20),
        route="KAPA-KBJC",
        total_time=1.3,
        pic_time=1.3,
        sic_time=0.0,
        dual_given=0.0,
        dual_received=0.0,
        cross_country=0.5,
        night=0.0,
        imc=0.0,
        simulated_instrument=0.0,
        landings=2,
        full_stop_landings_day=2,
        full_stop_landings_night=0,
        approaches=0,
        remarks=None,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_list_flights_applies_user_filter_and_pagination() -> None:
    current_user = SimpleNamespace(id=uuid4())
    session = _FakeSession([[ _flight_stub(), _flight_stub() ]])

    flights = await list_flights(current_user=current_user, session=session, limit=25, offset=10)

    assert len(flights) == 2
    compiled = session.statements[0].compile()
    assert compiled.params["user_id_1"] == current_user.id
    assert compiled.params["param_1"] == 25
    assert compiled.params["param_2"] == 10


@pytest.mark.asyncio
async def test_create_flight_links_new_record_to_current_user_and_aircraft() -> None:
    current_user = SimpleNamespace(id=uuid4())
    aircraft_id = uuid4()
    session = _FakeSession([SimpleNamespace(id=aircraft_id)])
    payload = FlightCreate(aircraft_id=aircraft_id, flight_date=date(2026, 4, 20), route="KAPA-KBJC", total_time=1.2)

    created = await create_flight(payload=payload, current_user=current_user, session=session)

    assert created.aircraft_id == aircraft_id
    assert session.added[0].user_id == current_user.id
    assert session.added[0].aircraft_id == aircraft_id
    assert session.committed is True


@pytest.mark.asyncio
async def test_create_flight_rejects_aircraft_owned_by_someone_else() -> None:
    current_user = SimpleNamespace(id=uuid4())
    payload = FlightCreate(aircraft_id=uuid4(), flight_date=date(2026, 4, 20))
    session = _FakeSession([None])

    with pytest.raises(HTTPException) as exc_info:
        await create_flight(payload=payload, current_user=current_user, session=session)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Aircraft must belong to the current user"


@pytest.mark.asyncio
async def test_get_flight_returns_404_for_missing_record() -> None:
    current_user = SimpleNamespace(id=uuid4())
    session = _FakeSession([None])

    with pytest.raises(HTTPException) as exc_info:
        await get_flight(flight_id=str(uuid4()), current_user=current_user, session=session)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Flight not found"
