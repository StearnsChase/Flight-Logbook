from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class TelemetryPoint:
    lat: float
    lon: float
    alt: Optional[float] = None
    timestamp: Optional[datetime] = None
    speed: Optional[float] = None
    
    # speed derivation could also be added as a utility method later


class TelemetryParserBase:
    def can_parse(self, data: str | bytes) -> bool:
        raise NotImplementedError()

    def parse(self, data: str | bytes) -> List[TelemetryPoint]:
        raise NotImplementedError()
