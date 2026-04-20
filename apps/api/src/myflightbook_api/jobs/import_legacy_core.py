from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select

from myflightbook_api.core.config import get_settings
from myflightbook_api.db.session import SessionLocal
from myflightbook_api.models.aircraft import Aircraft
from myflightbook_api.models.flight import Flight
from myflightbook_api.models.legacy import LegacyEntityMapping
from myflightbook_api.models.user import User
from myflightbook_api.services.importers.legacy_mysql import LegacyMySQLConfig, LegacyMySQLImporter

LEGACY_SYSTEM = "myflightbook-mysql"


@dataclass(slots=True)
class ImportSummary:
    users_processed: int = 0
    aircraft_processed: int = 0
    flights_processed: int = 0
    mappings_upserted: int = 0


def clean_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def fallback_email_for_legacy_user(row: dict[str, Any]) -> str:
    username = clean_string(row.get("Username")) or clean_string(row.get("PKID")) or "legacy-user"
    normalized = username.lower().replace(" ", ".")
    return f"{normalized}@legacy.myflightbook.local"


def build_user_display_name(row: dict[str, Any]) -> str:
    first_name = clean_string(row.get("FirstName"))
    last_name = clean_string(row.get("LastName"))
    if first_name or last_name:
        return " ".join(part for part in (first_name, last_name) if part)
    return clean_string(row.get("Username")) or "Legacy Pilot"


def build_aircraft_display_name(row: dict[str, Any]) -> str:
    tail_number = clean_string(row.get("tailnumber")) or "Unknown aircraft"
    version = clean_string(row.get("version"))
    return f"{tail_number} {version}" if version else tail_number


def coerce_decimal(value: Any) -> Decimal:
    if value in (None, ""):
        return Decimal("0")
    return Decimal(str(value))


def coerce_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(value)


def coerce_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raise ValueError(f"Unsupported flight date value: {value!r}")


def build_flight_payload(row: dict[str, Any], *, user_id: str, aircraft_id: str) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "aircraft_id": aircraft_id,
        "flight_date": coerce_date(row["date"]),
        "route": clean_string(row.get("Route")) or "",
        "remarks": clean_string(row.get("Comments")),
        "total_time": coerce_decimal(row.get("totalFlightTime")),
        "pic_time": coerce_decimal(row.get("PIC")),
        "sic_time": coerce_decimal(row.get("SIC")),
        "dual_given": coerce_decimal(row.get("cfi")),
        "dual_received": coerce_decimal(row.get("dualReceived")),
        "cross_country": coerce_decimal(row.get("crosscountry")),
        "night": coerce_decimal(row.get("night")),
        "imc": coerce_decimal(row.get("IMC")),
        "simulated_instrument": coerce_decimal(row.get("simulatedInstrument")),
        "landings": coerce_int(row.get("cLandings")),
        "full_stop_landings_day": coerce_int(row.get("cFullStopLandings")),
        "full_stop_landings_night": coerce_int(row.get("cNightLandings")),
        "approaches": coerce_int(row.get("cInstrumentApproaches")),
    }


def parse_canonical_id(value: str | None) -> UUID | None:
    if not value:
        return None
    return UUID(value)


async def get_mapping(
    session,
    *,
    legacy_table: str,
    legacy_identifier: str,
) -> LegacyEntityMapping | None:
    result = await session.execute(
        select(LegacyEntityMapping).where(
            LegacyEntityMapping.legacy_system == LEGACY_SYSTEM,
            LegacyEntityMapping.legacy_table == legacy_table,
            LegacyEntityMapping.legacy_identifier == legacy_identifier,
        )
    )
    return result.scalar_one_or_none()


async def upsert_mapping(
    session,
    *,
    legacy_table: str,
    legacy_identifier: str,
    entity_type: str,
    canonical_entity_id: str,
    mapping_metadata: dict[str, Any] | None = None,
) -> LegacyEntityMapping:
    mapping = await get_mapping(session, legacy_table=legacy_table, legacy_identifier=legacy_identifier)
    if mapping is None:
        mapping = LegacyEntityMapping(
            legacy_system=LEGACY_SYSTEM,
            legacy_table=legacy_table,
            legacy_identifier=legacy_identifier,
            entity_type=entity_type,
            canonical_entity_id=canonical_entity_id,
            mapping_metadata=mapping_metadata,
        )
        session.add(mapping)
    else:
        mapping.entity_type = entity_type
        mapping.canonical_entity_id = canonical_entity_id
        mapping.mapping_metadata = mapping_metadata

    await session.flush()
    return mapping


async def upsert_user(session, row: dict[str, Any], summary: ImportSummary) -> User:
    legacy_identifier = str(row["PKID"])
    username = clean_string(row.get("Username"))
    email = clean_string(row.get("Email")) or fallback_email_for_legacy_user(row)
    display_name = build_user_display_name(row)

    mapping = await get_mapping(session, legacy_table="users", legacy_identifier=legacy_identifier)
    user = await session.get(User, parse_canonical_id(mapping.canonical_entity_id)) if mapping else None

    if user is None:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

    if user is None and username:
        result = await session.execute(select(User).where(User.legacy_username == username))
        user = result.scalar_one_or_none()

    if user is None:
        user = User(email=email, display_name=display_name, locale="en-US")
        session.add(user)

    user.email = email
    user.display_name = display_name
    user.given_name = clean_string(row.get("FirstName"))
    user.family_name = clean_string(row.get("LastName"))
    user.legacy_username = username

    await session.flush()

    await upsert_mapping(
        session,
        legacy_table="users",
        legacy_identifier=legacy_identifier,
        entity_type="user",
        canonical_entity_id=str(user.id),
        mapping_metadata={"username": username, "email": email},
    )
    summary.mappings_upserted += 1
    summary.users_processed += 1
    return user


async def upsert_aircraft(session, *, user: User, row: dict[str, Any], summary: ImportSummary) -> Aircraft:
    legacy_identifier = str(row["idaircraft"])
    tail_number = clean_string(row.get("tailnumber")) or f"LEGACY-{legacy_identifier}"
    mapping = await get_mapping(session, legacy_table="aircraft", legacy_identifier=legacy_identifier)
    aircraft = await session.get(Aircraft, parse_canonical_id(mapping.canonical_entity_id)) if mapping else None

    if aircraft is None:
        result = await session.execute(
            select(Aircraft).where(
                Aircraft.owner_user_id == user.id,
                Aircraft.tail_number == tail_number,
            )
        )
        aircraft = result.scalar_one_or_none()

    if aircraft is None:
        aircraft = Aircraft(
            owner_user_id=user.id,
            tail_number=tail_number,
            display_name=build_aircraft_display_name(row),
        )
        session.add(aircraft)

    aircraft.tail_number = tail_number
    aircraft.display_name = build_aircraft_display_name(row)
    aircraft.model_name = clean_string(row.get("version"))

    await session.flush()

    await upsert_mapping(
        session,
        legacy_table="aircraft",
        legacy_identifier=legacy_identifier,
        entity_type="aircraft",
        canonical_entity_id=str(aircraft.id),
        mapping_metadata={"tail_number": tail_number},
    )
    summary.mappings_upserted += 1
    summary.aircraft_processed += 1
    return aircraft


async def upsert_flight(
    session,
    *,
    user: User,
    aircraft: Aircraft,
    row: dict[str, Any],
    summary: ImportSummary,
) -> Flight:
    legacy_identifier = str(row["idFlight"])
    payload = build_flight_payload(row, user_id=user.id, aircraft_id=aircraft.id)
    mapping = await get_mapping(session, legacy_table="flights", legacy_identifier=legacy_identifier)
    flight = await session.get(Flight, parse_canonical_id(mapping.canonical_entity_id)) if mapping else None

    if flight is None:
        result = await session.execute(
            select(Flight).where(
                Flight.user_id == user.id,
                Flight.aircraft_id == aircraft.id,
                Flight.flight_date == payload["flight_date"],
                Flight.route == payload["route"],
                Flight.total_time == payload["total_time"],
            )
        )
        flight = result.scalar_one_or_none()

    if flight is None:
        flight = Flight(**payload)
        session.add(flight)
    else:
        for field, value in payload.items():
            setattr(flight, field, value)

    await session.flush()

    await upsert_mapping(
        session,
        legacy_table="flights",
        legacy_identifier=legacy_identifier,
        entity_type="flight",
        canonical_entity_id=str(flight.id),
        mapping_metadata={"route": payload["route"], "flight_date": payload["flight_date"].isoformat()},
    )
    summary.mappings_upserted += 1
    summary.flights_processed += 1
    return flight


def _legacy_config_from_settings() -> LegacyMySQLConfig:
    settings = get_settings()
    required_fields = {
        "MFB_LEGACY_MYSQL_HOST": settings.legacy_mysql_host,
        "MFB_LEGACY_MYSQL_DATABASE": settings.legacy_mysql_database,
        "MFB_LEGACY_MYSQL_USERNAME": settings.legacy_mysql_username,
        "MFB_LEGACY_MYSQL_PASSWORD": settings.legacy_mysql_password,
    }
    missing = [name for name, value in required_fields.items() if not value]
    if missing:
        raise SystemExit(f"Missing legacy MySQL settings: {', '.join(missing)}")

    return LegacyMySQLConfig(
        username=settings.legacy_mysql_username or "",
        password=settings.legacy_mysql_password or "",
        host=settings.legacy_mysql_host or "",
        database=settings.legacy_mysql_database or "",
        port=settings.legacy_mysql_port,
    )


async def _run_import(limit_users: int, limit_flights: int, username: str | None) -> None:
    importer = LegacyMySQLImporter(_legacy_config_from_settings())
    if username:
        row = importer.fetch_user(username)
        raw_users = [row] if row else []
    else:
        raw_users = importer.fetch_users(limit=limit_users)

    summary = ImportSummary()

    async with SessionLocal() as session:
        for user_row in raw_users:
            user = await upsert_user(session, user_row, summary)
            aircraft_by_legacy_id: dict[str, Aircraft] = {}

            for aircraft_row in importer.fetch_aircraft_for_user(user.legacy_username or ""):
                aircraft = await upsert_aircraft(session, user=user, row=aircraft_row, summary=summary)
                aircraft_by_legacy_id[str(aircraft_row["idaircraft"])] = aircraft

            for flight_row in importer.fetch_flights_for_user(user.legacy_username or "", limit=limit_flights):
                legacy_aircraft_id = clean_string(flight_row.get("idaircraft"))
                if not legacy_aircraft_id:
                    continue
                aircraft = aircraft_by_legacy_id.get(legacy_aircraft_id)
                if aircraft is None:
                    continue
                await upsert_flight(session, user=user, aircraft=aircraft, row=flight_row, summary=summary)

        await session.commit()

    print(json.dumps(asdict(summary), indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Import core legacy MyFlightbook records into the canonical schema.")
    parser.add_argument("--limit-users", type=int, default=25, help="Maximum number of legacy users to import.")
    parser.add_argument("--limit-flights", type=int, default=5000, help="Maximum number of flights per imported user.")
    parser.add_argument("--username", help="Import a single legacy username instead of a user batch.")
    args = parser.parse_args()
    asyncio.run(_run_import(args.limit_users, args.limit_flights, args.username))


if __name__ == "__main__":
    main()
