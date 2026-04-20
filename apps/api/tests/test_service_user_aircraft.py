from __future__ import annotations

from uuid import uuid4

import pytest

from myflightbook_api.models.aircraft import Aircraft
from myflightbook_api.models.category_class import CatClassID
from myflightbook_api.models.country_code import CountryCodePrefix, HyphenPreference
from myflightbook_api.models.make_model import AllowedAircraftTypes, MakeModel, Manufacturer, TurbineLevel
from myflightbook_api.services.aircraft.user_aircraft import (
    UserAircraftConflictError,
    UserAircraftService,
    UserAircraftValidationError,
)


class _FakeScalarResult:
    def __init__(self, values):
        self._values = values

    def all(self):
        return list(self._values)


class _FakeExecuteResult:
    def __init__(self, value):
        self._value = value

    def scalars(self):
        return _FakeScalarResult(self._value)


class _FakeSession:
    def __init__(self, results: list[object]) -> None:
        self._results = iter(results)
        self.statements = []
        self.added = []

    async def execute(self, statement):
        self.statements.append(statement)
        return _FakeExecuteResult(next(self._results))

    def add(self, item) -> None:
        self.added.append(item)


def _country_codes() -> list[CountryCodePrefix]:
    return [
        CountryCodePrefix(country_name="United States", prefix="N", hyphen_pref=HyphenPreference.NO_HYPHEN),
        CountryCodePrefix(country_name="Canada", prefix="C", hyphen_pref=HyphenPreference.HYPHENATE),
        CountryCodePrefix(country_name="French Territories", prefix="F-OG", hyphen_pref=HyphenPreference.NO_HYPHEN),
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


@pytest.mark.asyncio
async def test_create_user_aircraft_normalizes_tail_and_projects_make_model() -> None:
    session = _FakeSession([[]])
    service = UserAircraftService(session)
    manufacturer = Manufacturer(id=11, name="Cessna")
    make_model = _make_model()

    aircraft = await service.create_user_aircraft(
        owner_user_id=uuid4(),
        tail_number="cfabc",
        display_name="Club Skyhawk",
        make_model=make_model,
        manufacturer=manufacturer,
        country_codes=_country_codes(),
    )

    assert aircraft.tail_number == "C-FABC"
    assert aircraft.display_name == "Club Skyhawk"
    assert aircraft.model_name == 'Cessna 172S "Skyhawk"'
    assert aircraft.category_class == "ASEL"
    assert aircraft.engine_type == "Piston"
    assert aircraft.is_complex is False
    assert aircraft.is_high_performance is True
    assert aircraft.is_retractable is False
    assert session.added == [aircraft]


@pytest.mark.asyncio
async def test_create_user_aircraft_rejects_duplicate_tail_for_same_user() -> None:
    owner_user_id = uuid4()
    existing = Aircraft(owner_user_id=owner_user_id, tail_number="C-FABC", display_name="Existing")
    existing.id = uuid4()
    session = _FakeSession([[existing]])
    service = UserAircraftService(session)

    with pytest.raises(UserAircraftConflictError, match="already exists"):
        await service.create_user_aircraft(
            owner_user_id=owner_user_id,
            tail_number="CFABC",
            display_name="Duplicate",
            country_codes=_country_codes(),
        )


@pytest.mark.asyncio
async def test_create_user_aircraft_rejects_invalid_country_suffix() -> None:
    session = _FakeSession([])
    service = UserAircraftService(session)

    with pytest.raises(UserAircraftValidationError, match="country prefix 'F-OG'"):
        await service.create_user_aircraft(
            owner_user_id=uuid4(),
            tail_number="F-OG",
            display_name="Broken",
            country_codes=_country_codes(),
        )


@pytest.mark.asyncio
async def test_create_user_aircraft_rejects_invalid_n_number() -> None:
    session = _FakeSession([])
    service = UserAircraftService(session)

    with pytest.raises(UserAircraftValidationError, match="valid N-number"):
        await service.create_user_aircraft(
            owner_user_id=uuid4(),
            tail_number="N10I",
            display_name="Broken",
            country_codes=_country_codes(),
        )


@pytest.mark.asyncio
async def test_update_user_aircraft_can_change_tail_and_fields() -> None:
    session = _FakeSession([[]])
    service = UserAircraftService(session)
    aircraft = Aircraft(owner_user_id=uuid4(), tail_number="N1234", display_name="Old Name")
    aircraft.id = uuid4()

    updated = await service.update_user_aircraft(
        aircraft,
        tail_number="n12345",
        display_name="Updated Name",
        is_complex=True,
        category_class="AMEL",
        country_codes=_country_codes(),
    )

    assert updated is aircraft
    assert aircraft.tail_number == "N12345"
    assert aircraft.display_name == "Updated Name"
    assert aircraft.is_complex is True
    assert aircraft.category_class == "AMEL"


@pytest.mark.asyncio
async def test_create_user_aircraft_rejects_sim_only_make_model() -> None:
    session = _FakeSession([[]])
    service = UserAircraftService(session)

    with pytest.raises(UserAircraftValidationError, match="Simulator-only"):
        await service.create_user_aircraft(
            owner_user_id=uuid4(),
            tail_number="N12345",
            display_name="Trainer",
            make_model=_make_model(allowed_types=AllowedAircraftTypes.SIMULATOR_ONLY),
            country_codes=_country_codes(),
        )
