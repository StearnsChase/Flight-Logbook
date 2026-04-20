from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from geoalchemy2.elements import WKTElement
from sqlalchemy.dialects import postgresql

from myflightbook_api.services.importers.airports import AirportImportRecord, AirportImporter


def test_map_row_supports_legacy_airports_table_columns() -> None:
    importer = AirportImporter()

    record = importer.map_row(
        {
            "airportID": "kapa",
            "FacilityName": "Centennial Airport",
            "Latitude": "39.570129",
            "Longitude": "-104.849294",
            "Type": "A",
            "SourceUserName": "legacy-pilot",
            "country": "US",
            "admin1": "CO",
        }
    )

    assert record == AirportImportRecord(
        code="KAPA",
        facility_type="A",
        name="Centennial Airport",
        latitude=Decimal("39.570129"),
        longitude=Decimal("-104.849294"),
        country="US",
        admin1="CO",
        source_user_name="legacy-pilot",
    )


def test_map_row_falls_back_to_csv_identifier_columns() -> None:
    importer = AirportImporter()

    record = importer.map_row(
        {
            "ICAO": "kapa",
            "FAA": "apa",
            "IATA": "",
            "Name": "Centennial Airport",
            "Latitude": "39.570129",
            "Longitude": "-104.849294",
            "Country": "US",
            "Admin1": "CO",
        }
    )

    assert record.code == "KAPA"
    assert record.facility_type == "A"
    assert record.country == "US"
    assert record.admin1 == "CO"


def test_prepare_batch_payloads_dedupes_rows_by_code_and_facility_type() -> None:
    importer = AirportImporter()
    source_user_id = uuid4()

    payloads = importer._prepare_batch_payloads(
        [
            AirportImportRecord(
                code="KAPA",
                facility_type="A",
                name="Old Name",
                latitude=Decimal("39.570129"),
                longitude=Decimal("-104.849294"),
                source_user_name="legacy-pilot",
            ),
            AirportImportRecord(
                code="KAPA",
                facility_type="A",
                name="New Name",
                latitude=Decimal("39.570130"),
                longitude=Decimal("-104.849295"),
                source_user_name="legacy-pilot",
            ),
        ],
        {"legacy-pilot": source_user_id},
    )

    assert len(payloads) == 1
    assert payloads[0]["name"] == "New Name"
    assert payloads[0]["source_user_id"] == source_user_id
    assert isinstance(payloads[0]["position"], WKTElement)
    assert payloads[0]["position"].data == "POINT(-104.849295 39.570130)"


def test_build_upsert_statement_uses_postgres_on_conflict_update() -> None:
    importer = AirportImporter()
    payloads = importer._prepare_batch_payloads(
        [
            AirportImportRecord(
                code="KAPA",
                facility_type="A",
                name="Centennial Airport",
                latitude=Decimal("39.570129"),
                longitude=Decimal("-104.849294"),
                country="US",
                admin1="CO",
            )
        ],
        {},
    )

    statement = importer.build_upsert_statement(payloads)
    compiled = str(statement.compile(dialect=postgresql.dialect()))

    assert "ON CONFLICT (code, facility_type) DO UPDATE SET" in compiled
    assert "source_user_id = excluded.source_user_id" in compiled
    assert "updated_at = now()" in compiled
