from __future__ import annotations

from dataclasses import dataclass

from myflightbook_api.models.media import TelemetryFormat


@dataclass(frozen=True, slots=True)
class TelemetryParserDefinition:
    name: TelemetryFormat
    legacy_module: str
    fixture_prefix: str


PARSER_REGISTRY: dict[TelemetryFormat, TelemetryParserDefinition] = {
    TelemetryFormat.AIRBLY: TelemetryParserDefinition(TelemetryFormat.AIRBLY, "MyFlightbook.Telemetry/Airbly.cs", "airbly"),
    TelemetryFormat.BAJU: TelemetryParserDefinition(TelemetryFormat.BAJU, "MyFlightbook.Telemetry/Baju.cs", "baju"),
    TelemetryFormat.CSV: TelemetryParserDefinition(TelemetryFormat.CSV, "MyFlightbook.Telemetry/CSV.cs", "csv"),
    TelemetryFormat.GPX: TelemetryParserDefinition(TelemetryFormat.GPX, "MyFlightbook.Telemetry/GPX.cs", "gpx"),
    TelemetryFormat.IGC: TelemetryParserDefinition(TelemetryFormat.IGC, "MyFlightbook.Telemetry/IGC.cs", "igc"),
    TelemetryFormat.KML: TelemetryParserDefinition(TelemetryFormat.KML, "MyFlightbook.Telemetry/KML.cs", "kml"),
    TelemetryFormat.NMEA: TelemetryParserDefinition(TelemetryFormat.NMEA, "MyFlightbook.Telemetry/NMEA.cs", "nmea")
}
