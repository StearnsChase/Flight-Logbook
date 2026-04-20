from __future__ import annotations

import re

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from myflightbook_api.models.aircraft import Aircraft
from myflightbook_api.models.category_class import CatClassID
from myflightbook_api.models.country_code import CountryCodePrefix, HyphenPreference
from myflightbook_api.models.make_model import AllowedAircraftTypes, MakeModel, Manufacturer, TurbineLevel


class UserAircraftValidationError(ValueError):
    pass


class UserAircraftConflictError(UserAircraftValidationError):
    pass


class UserAircraftService:
    MAX_TAIL_LENGTH = 10
    VALID_TAIL_RE = re.compile(r"^([A-Z0-9]+-?[A-Z0-9]+-?[A-Z0-9]+|N[1-9]\d?)$", re.IGNORECASE)
    VALID_N_NUMBER_RE = re.compile(r"^(N[^INO0][^IO]+|N[1-9]\d?)$", re.IGNORECASE)
    NORMALIZED_TAIL_CHARS_RE = re.compile(r"[^A-Z0-9]+")

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_user_aircraft(
        self,
        *,
        owner_user_id: UUID | str,
        tail_number: str,
        display_name: str | None = None,
        make_model: MakeModel | None = None,
        manufacturer: Manufacturer | None = None,
        model_name: str | None = None,
        category_class: str | None = None,
        engine_type: str | None = None,
        is_complex: bool | None = None,
        is_high_performance: bool | None = None,
        is_retractable: bool | None = None,
        country_codes: Sequence[CountryCodePrefix] | None = None,
    ) -> Aircraft:
        resolved_country_codes = list(country_codes) if country_codes is not None else await self._load_country_codes()
        normalized_tail = self.validate_and_normalize_tail_number(tail_number, resolved_country_codes)
        await self._ensure_tail_is_unique(owner_user_id, normalized_tail)

        aircraft = Aircraft(
            owner_user_id=owner_user_id,
            tail_number=normalized_tail,
            display_name=self._clean_display_name(display_name, normalized_tail),
        )
        self._apply_aircraft_details(
            aircraft,
            make_model=make_model,
            manufacturer=manufacturer,
            model_name=model_name,
            category_class=category_class,
            engine_type=engine_type,
            is_complex=is_complex,
            is_high_performance=is_high_performance,
            is_retractable=is_retractable,
        )
        self.session.add(aircraft)
        return aircraft

    async def update_user_aircraft(
        self,
        aircraft: Aircraft,
        *,
        tail_number: str | None = None,
        display_name: str | None = None,
        make_model: MakeModel | None = None,
        manufacturer: Manufacturer | None = None,
        model_name: str | None = None,
        category_class: str | None = None,
        engine_type: str | None = None,
        is_complex: bool | None = None,
        is_high_performance: bool | None = None,
        is_retractable: bool | None = None,
        country_codes: Sequence[CountryCodePrefix] | None = None,
    ) -> Aircraft:
        if tail_number is not None:
            resolved_country_codes = list(country_codes) if country_codes is not None else await self._load_country_codes()
            aircraft.tail_number = self.validate_and_normalize_tail_number(tail_number, resolved_country_codes)
            await self._ensure_tail_is_unique(aircraft.owner_user_id, aircraft.tail_number, exclude_aircraft_id=aircraft.id)

        if display_name is not None:
            aircraft.display_name = self._clean_display_name(display_name, aircraft.tail_number)

        self._apply_aircraft_details(
            aircraft,
            make_model=make_model,
            manufacturer=manufacturer,
            model_name=model_name,
            category_class=category_class,
            engine_type=engine_type,
            is_complex=is_complex,
            is_high_performance=is_high_performance,
            is_retractable=is_retractable,
        )
        return aircraft

    async def _load_country_codes(self) -> list[CountryCodePrefix]:
        result = await self.session.execute(select(CountryCodePrefix))
        return list(result.scalars().all())

    async def _ensure_tail_is_unique(
        self,
        owner_user_id: UUID | str,
        tail_number: str,
        *,
        exclude_aircraft_id: UUID | str | None = None,
    ) -> None:
        result = await self.session.execute(select(Aircraft).where(Aircraft.owner_user_id == owner_user_id))
        existing_aircraft = result.scalars().all()
        search_tail = self.normalize_tail_for_search(tail_number)

        for existing in existing_aircraft:
            if exclude_aircraft_id is not None and str(existing.id) == str(exclude_aircraft_id):
                continue
            if self.normalize_tail_for_search(existing.tail_number) == search_tail:
                raise UserAircraftConflictError("Tail number already exists for this user")

    def validate_and_normalize_tail_number(
        self,
        tail_number: str,
        country_codes: Sequence[CountryCodePrefix],
    ) -> str:
        cleaned_tail = (tail_number or "").strip().upper()
        if not cleaned_tail:
            raise UserAircraftValidationError("Tail number is required")

        country_code = CountryCodePrefix.best_match_country_code(cleaned_tail, list(country_codes))
        if country_code.is_sim:
            raise UserAircraftValidationError("Simulator registrations are not supported for user aircraft")
        if country_code.is_anonymous:
            raise UserAircraftValidationError("Anonymous registrations are not supported for user aircraft")

        normalized_tail = self._apply_country_hyphenation(cleaned_tail, country_code)

        if len(normalized_tail) > self.MAX_TAIL_LENGTH:
            raise UserAircraftValidationError(
                f"Tail number must be {self.MAX_TAIL_LENGTH} characters or fewer"
            )

        if not self.VALID_TAIL_RE.fullmatch(normalized_tail):
            raise UserAircraftValidationError(f"Tail number '{tail_number}' contains invalid characters")

        if normalized_tail.startswith("N") and not self.VALID_N_NUMBER_RE.fullmatch(normalized_tail):
            raise UserAircraftValidationError(f"Tail number '{tail_number}' is not a valid N-number")

        if country_code.prefix and len(self.normalize_tail_for_search(normalized_tail)) <= len(country_code.normalized_prefix):
            raise UserAircraftValidationError(
                f"Tail number must contain characters after the country prefix '{country_code.prefix}'"
            )

        return normalized_tail

    @classmethod
    def normalize_tail_for_search(cls, tail_number: str) -> str:
        return cls.NORMALIZED_TAIL_CHARS_RE.sub("", (tail_number or "").upper())

    def _apply_country_hyphenation(self, tail_number: str, country_code: CountryCodePrefix) -> str:
        if country_code.hyphen_pref == HyphenPreference.NONE or not country_code.normalized_prefix:
            return tail_number

        stripped_tail = self.normalize_tail_for_search(tail_number)
        return re.sub(
            f"^{re.escape(country_code.normalized_prefix)}",
            country_code.hyphenated_prefix,
            stripped_tail,
            count=1,
            flags=re.IGNORECASE,
        )

    def _apply_aircraft_details(
        self,
        aircraft: Aircraft,
        *,
        make_model: MakeModel | None,
        manufacturer: Manufacturer | None,
        model_name: str | None,
        category_class: str | None,
        engine_type: str | None,
        is_complex: bool | None,
        is_high_performance: bool | None,
        is_retractable: bool | None,
    ) -> None:
        if make_model is not None:
            self._validate_make_model(make_model)
            aircraft.model_name = self._display_model_name(make_model, manufacturer)
            aircraft.category_class = self._category_class_name(make_model)
            aircraft.engine_type = self._engine_type_name(make_model.engine_type)
            aircraft.is_complex = make_model.is_complex
            aircraft.is_high_performance = make_model.is_high_perf or make_model.is_200hp
            aircraft.is_retractable = make_model.is_retract

        if model_name is not None:
            aircraft.model_name = self._clean_optional_text(model_name)
        if category_class is not None:
            aircraft.category_class = self._clean_optional_text(category_class)
        if engine_type is not None:
            aircraft.engine_type = self._clean_optional_text(engine_type)
        if is_complex is not None:
            aircraft.is_complex = is_complex
        if is_high_performance is not None:
            aircraft.is_high_performance = is_high_performance
        if is_retractable is not None:
            aircraft.is_retractable = is_retractable

    def _validate_make_model(self, make_model: MakeModel) -> None:
        if make_model.allowed_types == AllowedAircraftTypes.SIMULATOR_ONLY:
            raise UserAircraftValidationError("Simulator-only make/models cannot be assigned to user aircraft")
        if make_model.allowed_types == AllowedAircraftTypes.SIM_OR_ANONYMOUS:
            raise UserAircraftValidationError("Simulator or anonymous make/models cannot be assigned to user aircraft")

    def _display_model_name(self, make_model: MakeModel, manufacturer: Manufacturer | None) -> str:
        model_display_name = make_model.model_display_name
        if manufacturer is None or not manufacturer.name:
            return model_display_name
        return f"{manufacturer.name} {model_display_name}".strip()

    def _category_class_name(self, make_model: MakeModel) -> str | None:
        try:
            return CatClassID(make_model.category_class_id).name
        except ValueError:
            return None

    def _engine_type_name(self, engine_type: TurbineLevel) -> str:
        labels = {
            TurbineLevel.PISTON: "Piston",
            TurbineLevel.TURBO_PROP: "Turbo Prop",
            TurbineLevel.JET: "Jet",
            TurbineLevel.UNSPECIFIED_TURBINE: "Turbine",
            TurbineLevel.ELECTRIC: "Electric",
        }
        return labels.get(engine_type, engine_type.name.replace("_", " ").title())

    def _clean_display_name(self, display_name: str | None, default_value: str) -> str:
        cleaned_display_name = self._clean_optional_text(display_name)
        return cleaned_display_name or default_value

    def _clean_optional_text(self, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None
