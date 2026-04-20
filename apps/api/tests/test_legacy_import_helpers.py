from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from myflightbook_api.jobs.import_legacy_core import (
    build_aircraft_display_name,
    build_flight_payload,
    build_user_display_name,
    fallback_email_for_legacy_user,
)


def test_legacy_user_helpers_fill_missing_identity_data() -> None:
    row = {"PKID": 42, "Username": "LegacyPilot", "FirstName": None, "LastName": None, "Email": None}

    assert fallback_email_for_legacy_user(row) == "legacypilot@legacy.myflightbook.local"
    assert build_user_display_name(row) == "LegacyPilot"


def test_build_aircraft_display_name_prefers_tail_and_version() -> None:
    row = {"tailnumber": "N42MFB", "version": "C172S"}
    assert build_aircraft_display_name(row) == "N42MFB C172S"


def test_build_flight_payload_maps_legacy_columns_to_canonical_fields() -> None:
    row = {
        "date": datetime(2026, 4, 17, 15, 30, 0),
        "Route": "KAPA KBJC",
        "Comments": "Legacy import",
        "totalFlightTime": "1.4",
        "PIC": "1.4",
        "SIC": None,
        "cfi": "0.2",
        "dualReceived": "0.3",
        "crosscountry": "0.8",
        "night": "",
        "IMC": "0.1",
        "simulatedInstrument": "0.2",
        "cLandings": 2,
        "cFullStopLandings": 2,
        "cNightLandings": 0,
        "cInstrumentApproaches": 1,
    }

    payload = build_flight_payload(row, user_id="user-id", aircraft_id="aircraft-id")

    assert payload["flight_date"] == date(2026, 4, 17)
    assert payload["total_time"] == Decimal("1.4")
    assert payload["dual_given"] == Decimal("0.2")
    assert payload["dual_received"] == Decimal("0.3")
    assert payload["night"] == Decimal("0")
    assert payload["landings"] == 2
