from __future__ import annotations

import csv
import re

from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import sqlalchemy as sa

from geoalchemy2.elements import WKTElement
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from myflightbook_api.models.airport import Airport
from myflightbook_api.models.user import User
from myflightbook_api.services.importers.legacy_mysql import LegacyMySQLImporter

LEGACY_AIRPORTS_QUERY = text(
    """
    SELECT airportID, FacilityName, Latitude, Longitude, Type, SourceUserName, country, admin1
    FROM airports
    ORDER BY airportID ASC, Type ASC
    """
)

_NON_ALNUM = re.compile(r"[^A-Za-z0-9]+")


@dataclass(slots=True, frozen=True)
class AirportImportRecord:
    code: str
    facility_type: str
    name: str
    latitude: Decimal
    longitude: Decimal
    country: str | None = None
    admin1: str | None = None
    source_user_name: str | None = None


@dataclass(slots=True)
class AirportImportSummary:
    rows_read: int = 0
    rows_valid: int = 0
    rows_skipped: int = 0
    rows_upserted: int = 0
    batches_executed: int = 0


def _clean_string(value: Any) -> str | None:
    if value is None:
        return None

    text_value = str(value).strip()
    return text_value or None


def _normalize_code(value: Any, *, strip_non_alnum: bool = False) -> str | None:
    text_value = _clean_string(value)
    if text_value is None:
        return None

    if strip_non_alnum:
        text_value = _NON_ALNUM.sub("", text_value)

    text_value = text_value.upper()
    return text_value or None


def _coerce_decimal(value: Any, *, field_name: str) -> Decimal:
    text_value = _clean_string(value)
    if text_value is None:
        raise ValueError(f"Airport import row is missing {field_name}.")

    try:
        return Decimal(text_value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid {field_name} value: {value!r}") from exc


def _first_present(row: Mapping[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return None


class AirportImporter:
    def __init__(self, *, batch_size: int = 1000, strict: bool = False) -> None:
        if batch_size < 1:
            raise ValueError("batch_size must be greater than zero")

        self.batch_size = batch_size
        self.strict = strict

    def stream_legacy_rows(self, legacy_importer: LegacyMySQLImporter) -> Iterator[dict[str, Any]]:
        with legacy_importer.engine.connect().execution_options(stream_results=True) as connection:
            result = connection.execute(LEGACY_AIRPORTS_QUERY).mappings()
            for row in result:
                yield dict(row)

    def stream_csv_rows(self, csv_path: str | Path) -> Iterator[dict[str, str]]:
        path = Path(csv_path)
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                raise ValueError(f"CSV file {path} does not include a header row.")

            for row in reader:
                yield {key: (value or "") for key, value in row.items() if key is not None}

    def map_row(self, row: Mapping[str, Any]) -> AirportImportRecord:
        code = _normalize_code(_first_present(row, ("airportID", "AirportID", "airportid", "code", "Code")))
        if code is None:
            code = _normalize_code(_first_present(row, ("ICAO", "icao")), strip_non_alnum=True)
        if code is None:
            code = _normalize_code(_first_present(row, ("FAA", "faa")), strip_non_alnum=True)
        if code is None:
            code = _normalize_code(_first_present(row, ("IATA", "iata")), strip_non_alnum=True)
        if code is None:
            raise ValueError("Airport import row is missing a usable airport code.")

        name = _clean_string(_first_present(row, ("FacilityName", "facilityname", "facility_name", "Name", "name")))
        if name is None:
            raise ValueError(f"Airport {code} is missing a facility name.")

        facility_type = _normalize_code(
            _first_present(row, ("Type", "type", "facility_type", "FacilityTypeCode", "facilitytypecode", "FacilityType"))
        ) or "A"

        latitude = _coerce_decimal(_first_present(row, ("Latitude", "latitude")), field_name="latitude")
        longitude = _coerce_decimal(_first_present(row, ("Longitude", "longitude")), field_name="longitude")

        return AirportImportRecord(
            code=code,
            facility_type=facility_type,
            name=name,
            latitude=latitude,
            longitude=longitude,
            country=_clean_string(_first_present(row, ("country", "Country"))),
            admin1=_clean_string(_first_present(row, ("admin1", "Admin1"))),
            source_user_name=_clean_string(
                _first_present(row, ("SourceUserName", "sourceusername", "source_user_name", "UserName"))
            ),
        )

    async def import_legacy_rows(
        self,
        session: AsyncSession,
        legacy_importer: LegacyMySQLImporter,
        *,
        commit: bool = False,
    ) -> AirportImportSummary:
        return await self.import_rows(session, self.stream_legacy_rows(legacy_importer), commit=commit)

    async def import_csv(
        self,
        session: AsyncSession,
        csv_path: str | Path,
        *,
        commit: bool = False,
    ) -> AirportImportSummary:
        return await self.import_rows(session, self.stream_csv_rows(csv_path), commit=commit)

    async def import_rows(
        self,
        session: AsyncSession,
        rows: Iterable[Mapping[str, Any]],
        *,
        commit: bool = False,
    ) -> AirportImportSummary:
        summary = AirportImportSummary()
        batch: list[AirportImportRecord] = []

        for row in rows:
            summary.rows_read += 1

            try:
                batch.append(self.map_row(row))
            except ValueError:
                summary.rows_skipped += 1
                if self.strict:
                    raise
                continue

            summary.rows_valid += 1
            if len(batch) >= self.batch_size:
                summary.rows_upserted += await self._upsert_batch(session, batch)
                summary.batches_executed += 1
                batch.clear()

        if batch:
            summary.rows_upserted += await self._upsert_batch(session, batch)
            summary.batches_executed += 1

        if commit:
            await session.commit()

        return summary

    async def _resolve_source_users(
        self,
        session: AsyncSession,
        rows: Sequence[AirportImportRecord],
    ) -> dict[str, UUID]:
        usernames = sorted({row.source_user_name for row in rows if row.source_user_name})
        if not usernames:
            return {}

        result = await session.execute(
            select(User.legacy_username, User.id).where(User.legacy_username.in_(usernames))
        )
        return {
            str(legacy_username): user_id
            for legacy_username, user_id in result.all()
            if legacy_username is not None
        }

    def _prepare_batch_payloads(
        self,
        rows: Sequence[AirportImportRecord],
        source_user_ids: Mapping[str, UUID],
    ) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        payloads_by_key: dict[tuple[str, str], dict[str, Any]] = {}

        for row in rows:
            payloads_by_key[(row.code, row.facility_type)] = {
                "id": uuid4(),
                "code": row.code,
                "facility_type": row.facility_type,
                "name": row.name,
                "country": row.country,
                "admin1": row.admin1,
                "latitude": row.latitude,
                "longitude": row.longitude,
                "position": WKTElement(f"POINT({row.longitude} {row.latitude})", srid=4326),
                "source_user_id": source_user_ids.get(row.source_user_name or ""),
                "created_at": now,
                "updated_at": now,
            }

        return list(payloads_by_key.values())

    def build_upsert_statement(self, payloads: Sequence[Mapping[str, Any]]) -> sa.Executable:
        if not payloads:
            raise ValueError("Cannot build an airport upsert statement with no payloads.")

        statement = insert(Airport).values(list(payloads))
        excluded = statement.excluded

        return statement.on_conflict_do_update(
            index_elements=[Airport.code, Airport.facility_type],
            set_={
                "name": excluded.name,
                "country": excluded.country,
                "admin1": excluded.admin1,
                "latitude": excluded.latitude,
                "longitude": excluded.longitude,
                "position": excluded.position,
                "source_user_id": excluded.source_user_id,
                "updated_at": sa.func.now(),
            },
        )

    async def _upsert_batch(self, session: AsyncSession, rows: Sequence[AirportImportRecord]) -> int:
        if not rows:
            return 0

        source_user_ids = await self._resolve_source_users(session, rows)
        payloads = self._prepare_batch_payloads(rows, source_user_ids)
        statement = self.build_upsert_statement(payloads)
        await session.execute(statement)
        return len(payloads)
