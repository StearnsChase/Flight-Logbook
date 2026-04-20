import pytest
from datetime import datetime, timezone
from myflightbook_api.services.telemetry.nmea import NMEAParser

SAMPLE_NMEA = """$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47
$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230323,003.1,W*6A
$GPGGA,123520,4807.040,N,01131.010,E,1,08,0.9,546.0,M,46.9,M,,*48
$GPRMC,123520,A,4807.040,N,01131.010,E,025.0,084.4,230323,003.1,W*6B
"""

def test_nmea_can_parse():
    parser = NMEAParser()
    assert parser.can_parse(SAMPLE_NMEA)
    assert not parser.can_parse("Not an NMEA file")

def test_nmea_parse():
    parser = NMEAParser()
    points = parser.parse(SAMPLE_NMEA)
    
    assert len(points) == 2
    
    p1 = points[0]
    # 4807.038,N -> 48 + 7.038/60 = 48.1173
    # 01131.000,E -> 11 + 31.000/60 = 11.5166...
    assert round(p1.lat, 4) == 48.1173
    assert round(p1.lon, 4) == 11.5167
    # 545.4 M -> feet = 545.4 * 3.280839895013123 = 1789.369...
    assert round(p1.alt, 2) == 1789.37
    assert p1.timestamp == datetime(2023, 3, 23, 12, 35, 19, tzinfo=timezone.utc)
    assert p1.speed == 22.4
    
    p2 = points[1]
    assert round(p2.lat, 4) == 48.1173
    assert round(p2.lon, 4) == 11.5168
    # 546.0 M -> 546 * 3.280839895013123 = 1791.338...
    assert round(p2.alt, 2) == 1791.34
    assert p2.timestamp == datetime(2023, 3, 23, 12, 35, 20, tzinfo=timezone.utc)
    assert p2.speed == 25.0
