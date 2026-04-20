from __future__ import annotations

from myflightbook_api.models.media import TelemetryFormat
from myflightbook_api.services.telemetry.parsers import PARSER_REGISTRY


def test_all_v1_telemetry_formats_have_registry_entries() -> None:
    expected = {
        TelemetryFormat.AIRBLY,
        TelemetryFormat.BAJU,
        TelemetryFormat.CSV,
        TelemetryFormat.GPX,
        TelemetryFormat.IGC,
        TelemetryFormat.KML,
        TelemetryFormat.NMEA
    }

    assert expected.issubset(set(PARSER_REGISTRY.keys()))
