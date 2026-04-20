import pytest
from datetime import datetime, timezone, timedelta
from myflightbook_api.services.telemetry.baju import BajuParser

SAMPLE_BAJU = """Copyright 2023 BajuSoftware
Some other header line
Date/Time: 1/1/2023 12:00:00 PM

ElapsedSeconds,Latitude,Longitude,Altitude (Feet Ind),Airspeed (Knots Ind)
0,47.6,-122.3,100,50
60,47.61,-122.31,150,55
"""

def test_baju_can_parse():
    parser = BajuParser()
    assert parser.can_parse(SAMPLE_BAJU)
    assert not parser.can_parse("Not Baju CSV")

def test_baju_parse():
    parser = BajuParser()
    points = parser.parse(SAMPLE_BAJU)
    
    assert len(points) == 2
    
    p1 = points[0]
    assert p1.lat == 47.6
    assert p1.lon == -122.3
    assert p1.alt == 100.0
    assert p1.speed == 50.0
    # Base date: 1/1/2023 12:00:00 PM UTC + 0 seconds
    assert p1.timestamp == datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    
    p2 = points[1]
    assert p2.lat == 47.61
    assert p2.lon == -122.31
    assert p2.alt == 150.0
    assert p2.speed == 55.0
    # + 60 seconds
    assert p2.timestamp == datetime(2023, 1, 1, 12, 1, 0, tzinfo=timezone.utc)
