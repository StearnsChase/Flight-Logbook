import pytest
from datetime import datetime, timezone
from myflightbook_api.services.telemetry.csv import CSVTelemetryParser

SAMPLE_STANDARD_CSV = """LAT,LON,ALT,SPEED,DATE,TIME
47.6062,-122.3321,100,50,2023-01-01,12:00:00
47.6100,-122.3300,150,55,2023-01-01,12:01:00
"""

SAMPLE_GARMIN_CSV = """#airframe_info, bla bla
Date (yyyy-mm-dd),UTC Time (hh:mm:ss),Latitude (deg),Longitude (deg),GPS Altitude (ft)
Lcl Date,UTC Time,Latitude,Longitude,AltGPS
2023-01-01,12:00:00,47.6,-122.3,100
"""

SAMPLE_BROKEN_CSV = """LAT,LON,PALT,SPEED,HERROR,DATE,COMMENT
47,6062,-122,3321,100,50,5,10,5,"2023-01-01 12:00","Test"
"""

def test_csv_can_parse():
    parser = CSVTelemetryParser()
    assert parser.can_parse("anything")

def test_csv_parse_standard():
    parser = CSVTelemetryParser()
    points = parser.parse(SAMPLE_STANDARD_CSV)
    
    assert len(points) == 2
    
    p1 = points[0]
    assert p1.lat == 47.6062
    assert p1.lon == -122.3321
    assert p1.alt == 100.0
    assert p1.speed == 50.0
    assert p1.timestamp == datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    
def test_csv_parse_garmin():
    parser = CSVTelemetryParser()
    points = parser.parse(SAMPLE_GARMIN_CSV)
    
    assert len(points) == 1
    p1 = points[0]
    assert p1.lat == 47.6
    assert p1.lon == -122.3
    assert p1.alt == 100.0
    # Garmin header merging creates "UTC Date" and "UTC Time"
    assert p1.timestamp == datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    
def test_csv_parse_broken():
    parser = CSVTelemetryParser()
    points = parser.parse(SAMPLE_BROKEN_CSV)
    
    assert len(points) == 1
    p1 = points[0]
    assert p1.lat == 47.6062
    assert p1.lon == -122.3321
    assert p1.alt == 100.0
    # The broken csv row hack maps speed to idx 5, 6
    assert p1.speed == 50.5
