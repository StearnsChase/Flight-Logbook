import pytest
from datetime import datetime, timezone
from myflightbook_api.services.telemetry.gpx import GPXParser

SAMPLE_GPX = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="MyFlightbook" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <trkseg>
      <trkpt lat="47.6062" lon="-122.3321">
        <ele>100.5</ele>
        <time>2023-01-01T12:00:00Z</time>
      </trkpt>
      <trkpt lat="47.6100" lon="-122.3300">
        <ele>150.0</ele>
        <time>2023-01-01T12:01:00Z</time>
        <speed>50.5</speed>
      </trkpt>
      <trkpt lat="47.6150" lon="-122.3200">
        <time>2023-01-01T12:02:00Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>
"""

SAMPLE_BAD_ELF = """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1" xmlns:badelf="http://bad-elf.com/xmlschemas/GpxExtensionsV1">
  <trk>
    <trkseg>
      <trkpt lat="47.6" lon="-122.3">
        <extensions>
          <badelf:speed>45.2</badelf:speed>
        </extensions>
      </trkpt>
    </trkseg>
  </trk>
</gpx>
"""

def test_gpx_can_parse():
    parser = GPXParser()
    assert parser.can_parse(SAMPLE_GPX)
    assert not parser.can_parse("Not a GPX file")
    assert parser.can_parse(SAMPLE_BAD_ELF)

def test_gpx_parse_standard():
    parser = GPXParser()
    points = parser.parse(SAMPLE_GPX)
    
    assert len(points) == 3
    
    p1 = points[0]
    assert p1.lat == 47.6062
    assert p1.lon == -122.3321
    assert p1.alt == 100.5
    assert p1.timestamp == datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    # Speed is not present in first point, and since second point HAS speed, no speed derived for entire file (matching C# logic)
    assert p1.speed is None 
    
    p2 = points[1]
    assert p2.lat == 47.6100
    assert p2.speed == 50.5
    
    p3 = points[2]
    assert p3.speed is None
    
def test_gpx_parse_bad_elf_speed():
    parser = GPXParser()
    points = parser.parse(SAMPLE_BAD_ELF)
    
    assert len(points) == 1
    assert points[0].speed == 45.2
