from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List

from myflightbook_api.services.telemetry.base import TelemetryParserBase, TelemetryPoint

class AirblyParser(TelemetryParserBase):
    def can_parse(self, data: str | bytes) -> bool:
        if isinstance(data, bytes):
            try:
                data_str = data.decode("utf-8")
            except UnicodeDecodeError:
                return False
        else:
            data_str = data
            
        if not data_str:
            return False

        data_str = data_str.strip()
        return data_str.startswith("{") and "happenedAt" in data_str

    def parse(self, data: str | bytes) -> List[TelemetryPoint]:
        if isinstance(data, bytes):
            try:
                data_str = data.decode("utf-8")
            except UnicodeDecodeError:
                raise ValueError("Data to parse is not valid UTF-8 JSON")
        else:
            data_str = data
            
        if not data_str:
            raise ValueError("No data to parse")
            
        try:
            ar = json.loads(data_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid Airbly JSON: {e}")
            
        if "points" not in ar or not isinstance(ar["points"], dict):
            return []
            
        raw_points = list(ar["points"].values())
        # Sort by happenedAt
        raw_points.sort(key=lambda x: x.get("happenedAt", 0))
        
        points: List[TelemetryPoint] = []
        for ap in raw_points:
            happened_at = ap.get("happenedAt", 0)
            timestamp = datetime.fromtimestamp(happened_at, tz=timezone.utc)
            
            lat = ap.get("latitude", 0.0)
            lon = ap.get("longitude", 0.0)
            alt = ap.get("altitude", 0.0) # In Feet
            
            # The legacy code didn't assign speed for Airbly
            points.append(TelemetryPoint(lat=lat, lon=lon, alt=alt, timestamp=timestamp))
            
        return points
