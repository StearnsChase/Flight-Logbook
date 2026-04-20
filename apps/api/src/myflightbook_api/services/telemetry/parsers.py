from __future__ import annotations

from dataclasses import dataclass
from typing import Type

from myflightbook_api.models.media import TelemetryFormat
from myflightbook_api.services.telemetry.base import TelemetryParserBase, TelemetryPoint
from myflightbook_api.services.telemetry.airbly import AirblyParser
from myflightbook_api.services.telemetry.baju import BajuParser
from myflightbook_api.services.telemetry.csv import CSVTelemetryParser
from myflightbook_api.services.telemetry.gpx import GPXParser
from myflightbook_api.services.telemetry.igc import IGCParser
from myflightbook_api.services.telemetry.kml import KMLParser
from myflightbook_api.services.telemetry.nmea import NMEAParser


@dataclass(frozen=True, slots=True)
class TelemetryParserDefinition:
    name: TelemetryFormat
    legacy_module: str
    fixture_prefix: str
    parser_class: Type[TelemetryParserBase]


PARSER_REGISTRY: dict[TelemetryFormat, TelemetryParserDefinition] = {
    TelemetryFormat.AIRBLY: TelemetryParserDefinition(TelemetryFormat.AIRBLY, "MyFlightbook.Telemetry/Airbly.cs", "airbly", AirblyParser),
    TelemetryFormat.BAJU: TelemetryParserDefinition(TelemetryFormat.BAJU, "MyFlightbook.Telemetry/Baju.cs", "baju", BajuParser),
    TelemetryFormat.CSV: TelemetryParserDefinition(TelemetryFormat.CSV, "MyFlightbook.Telemetry/CSV.cs", "csv", CSVTelemetryParser),
    TelemetryFormat.GPX: TelemetryParserDefinition(TelemetryFormat.GPX, "MyFlightbook.Telemetry/GPX.cs", "gpx", GPXParser),
    TelemetryFormat.IGC: TelemetryParserDefinition(TelemetryFormat.IGC, "MyFlightbook.Telemetry/IGC.cs", "igc", IGCParser),
    TelemetryFormat.KML: TelemetryParserDefinition(TelemetryFormat.KML, "MyFlightbook.Telemetry/KML.cs", "kml", KMLParser),
    TelemetryFormat.NMEA: TelemetryParserDefinition(TelemetryFormat.NMEA, "MyFlightbook.Telemetry/NMEA.cs", "nmea", NMEAParser)
}


def parse_telemetry_data(data: str | bytes) -> tuple[TelemetryFormat, list[TelemetryPoint]]:
    # For now, evaluate in standard order, CSV last as it can parse almost anything
    eval_order = [
        TelemetryFormat.GPX,
        TelemetryFormat.KML,
        TelemetryFormat.IGC,
        TelemetryFormat.NMEA,
        TelemetryFormat.BAJU,
        TelemetryFormat.AIRBLY,
        TelemetryFormat.CSV
    ]
    
    for fmt in eval_order:
        parser_def = PARSER_REGISTRY[fmt]
        parser = parser_def.parser_class()
        if parser.can_parse(data):
            try:
                points = parser.parse(data)
                if points:
                    return fmt, points
            except Exception:
                # If parsing fails, we could continue to try other parsers or just fail
                pass
                
    raise ValueError("No parser could successfully parse the provided telemetry data.")
