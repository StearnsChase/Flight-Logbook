import pytest
from datetime import datetime, timezone
from myflightbook_api.services.telemetry.airbly import AirblyParser

SAMPLE_AIRBLY = """{
  "cmd": "points",
  "points": {
    "uuid1": {
      "happenedAt": 1672574400,
      "latitude": 47.6,
      "longitude": -122.3,
      "altitude": 100
    },
    "uuid2": {
      "happenedAt": 1672574460,
      "latitude": 47.61,
      "longitude": -122.31,
      "altitude": 150
    }
  }
}"""

def test_airbly_can_parse():
    parser = AirblyParser()
    assert parser.can_parse(SAMPLE_AIRBLY)
    assert not parser.can_parse("{}")

def test_airbly_parse():
    parser = AirblyParser()
    points = parser.parse(SAMPLE_AIRBLY)
    
    assert len(points) == 2
    
    p1 = points[0]
    assert p1.lat == 47.6
    assert p1.lon == -122.3
    assert p1.alt == 100.0
    assert p1.timestamp == datetime.fromtimestamp(1672574400, tz=timezone.utc)
    assert p1.speed is None
    
    p2 = points[1]
    assert p2.lat == 47.61
    assert p2.lon == -122.31
    assert p2.alt == 150.0
    assert p2.timestamp == datetime.fromtimestamp(1672574460, tz=timezone.utc)
    assert p2.speed is None
