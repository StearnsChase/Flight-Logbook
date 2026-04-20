import pytest
from datetime import datetime, timezone
from myflightbook_api.services.telemetry.igc import IGCParser

SAMPLE_IGC = """AXGD123
HFDTE230123
B1200004736372N12219926WA0010000200
B1201004736600N12219800WA0015000250
"""

def test_igc_can_parse():
    parser = IGCParser()
    assert parser.can_parse(SAMPLE_IGC)
    assert not parser.can_parse("Not an IGC file")
    assert not parser.can_parse("AXGD123\nBut no date")

def test_igc_parse():
    parser = IGCParser()
    points = parser.parse(SAMPLE_IGC)
    
    assert len(points) == 2
    
    # B 12 00 00 47 36372 N 122 19926 W A 00100 00200
    # lat: 47 + 36.372 / 60 = 47.6062
    # lon: -(122 + 19.926 / 60) = -122.3321
    # alt: 100
    
    p1 = points[0]
    assert round(p1.lat, 4) == 47.6062
    assert round(p1.lon, 4) == -122.3321
    assert p1.alt == 100.0
    assert p1.timestamp == datetime(2023, 1, 23, 12, 0, 0, tzinfo=timezone.utc)
    
    # B 12 01 00 47 36600 N 122 19800 W A 00150 00250
    # lat: 47 + 36.600 / 60 = 47.6100
    # lon: -(122 + 19.800 / 60) = -122.3300
    # alt: 150
    
    p2 = points[1]
    assert round(p2.lat, 4) == 47.6100
    assert round(p2.lon, 4) == -122.3300
    assert p2.alt == 150.0
    assert p2.timestamp == datetime(2023, 1, 23, 12, 1, 0, tzinfo=timezone.utc)
