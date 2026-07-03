from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from myflightbook_api.models.airport import Airport
from myflightbook_api.services.geography import airports as airport_service
from myflightbook_api.services.geography.airports import AdHocFix, AirportQueryService


class _FakeScalarResult:
    def __init__(self, values):
        self._values = values

    def all(self):
        return list(self._values)


class _FakeExecuteResult:
    def __init__(self, values) -> None:
        self._values = values

    def scalars(self):
        return _FakeScalarResult(self._values)


class _FakeSession:
    def __init__(self, values) -> None:
        self.values = values
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        return _FakeExecuteResult(self.values)


class _FakeSessionContext:
    def __init__(self, session: _FakeSession) -> None:
        self.session = session

    async def __aenter__(self) -> _FakeSession:
        return self.session

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


def _airport(code: str) -> Airport:
    airport = Airport(
        code=code,
        facility_type="A",
        name=f"{code} Airport",
        latitude=Decimal("47.000000"),
        longitude=Decimal("-122.000000"),
    )
    airport.id = uuid4()
    return airport


@pytest.mark.asyncio
async def test_airports_matching_codes_handles_adhoc_and_us_aliases(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession([_airport("KSEA"), _airport("SEA"), _airport("LAX")])
    monkeypatch.setattr(airport_service, "SessionLocal", lambda: _FakeSessionContext(session))

    results = await AirportQueryService.airports_matching_codes(["KSEA", "@LAX", "@47.60620000N122.33210000W"])

    assert isinstance(results[0], AdHocFix)
    compiled = str(session.statements[0].compile(compile_kwargs={"literal_binds": True}))
    assert "'KSEA'" in compiled
    assert "'SEA'" in compiled
    assert "'LAX'" in compiled

