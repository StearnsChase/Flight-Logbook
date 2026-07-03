from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from myflightbook_api.models.user import User
from myflightbook_api.services.importers.flights import GenericCSVImporter, ImportOrchestratorService


class _FakeScalars:
    def __init__(self, values) -> None:
        self._values = values

    def all(self):
        return list(self._values)


class _FakeExecuteResult:
    def __init__(self, values) -> None:
        self._values = values

    def scalars(self) -> _FakeScalars:
        return _FakeScalars(self._values)


class _FakeSession:
    def __init__(self) -> None:
        self.added = []
        self.committed = False
        self.refreshed = []

    async def execute(self, statement):
        return _FakeExecuteResult([])

    def add(self, item) -> None:
        if getattr(item, "id", None) is None:
            item.id = uuid4()
        self.added.append(item)

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, item) -> None:
        self.refreshed.append(item)


def test_generic_importer_uses_heuristic_column_mapping() -> None:
    user = User(email="pilot@example.com", display_name="Pilot Example")
    user.id = uuid4()
    importer = GenericCSVImporter(user)
    file_content = """Date,Tail,Route,Total,PIC,Landings,Remarks
2026-04-20,N777GT,KAPA-KBJC,1.3,1.0,2,Generic import
"""

    result = importer.parse_file(file_content)

    assert result.success is True
    assert len(result.imported_flights) == 1
    flight = result.imported_flights[0]
    assert flight.aircraft.tail_number == "N777GT"
    assert flight.route == "KAPA-KBJC"
    assert float(flight.total_time) == 1.3
    assert flight.landings == 2


@pytest.mark.asyncio
async def test_import_orchestrator_selects_an_importer_and_persists_results() -> None:
    user = User(email="pilot@example.com", display_name="Pilot Example")
    user.id = uuid4()
    session = _FakeSession()
    file_content = """Date,Tail,Route,Total,PIC,Landings
2026-04-20,N900QX,KDEN-KAPA,1.1,1.0,1
"""

    result = await ImportOrchestratorService.import_flights_from_csv(file_content, user, session)

    assert result.success is True
    assert len(result.imported_flights) == 1
    assert session.committed is True
    assert len(session.added) >= 2
    assert result.imported_flights[0] in session.refreshed
