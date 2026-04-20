import pytest
from datetime import datetime, timezone
from myflightbook_api.services.telemetry.kml import KMLParser

SAMPLE_KML_V1 = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <LineString>
        <coordinates>
          -122.3321,47.6062,100.5 -122.3300,47.6100,150.0 -122.3200,47.6150
        </coordinates>
      </LineString>
    </Placemark>
  </Document>
</kml>
"""

SAMPLE_KML_V2 = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">
  <Document>
    <Placemark>
      <gx:Track>
        <when>2023-01-01T12:00:00Z</when>
        <when>2023-01-01T12:01:00Z</when>
        <gx:coord>-122.3321 47.6062 100.5</gx:coord>
        <gx:coord>-122.3300 47.6100 150.0</gx:coord>
      </gx:Track>
    </Placemark>
    <gx:SimpleArrayData name="speedKts">
      <gx:value>45.5</gx:value>
      <gx:value>50.2</gx:value>
    </gx:SimpleArrayData>
  </Document>
</kml>
"""

def test_kml_can_parse():
    parser = KMLParser()
    assert parser.can_parse(SAMPLE_KML_V1)
    assert parser.can_parse(SAMPLE_KML_V2)
    assert not parser.can_parse("Not a KML file")

def test_kml_parse_v1():
    parser = KMLParser()
    points = parser.parse(SAMPLE_KML_V1)
    
    assert len(points) == 3
    
    # KMLv1 points have no timestamps or speed, just lat, lon, alt
    p1 = points[0]
    assert p1.lat == 47.6062
    assert p1.lon == -122.3321
    assert p1.alt == 100.5
    assert p1.timestamp is None
    assert p1.speed is None
    
    p2 = points[1]
    assert p2.lat == 47.6100
    assert p2.lon == -122.3300
    assert p2.alt == 150.0
    
    p3 = points[2]
    assert p3.lat == 47.6150
    assert p3.lon == -122.3200
    assert p3.alt is None

def test_kml_parse_v2():
    parser = KMLParser()
    points = parser.parse(SAMPLE_KML_V2)
    
    assert len(points) == 2
    
    p1 = points[0]
    assert p1.lat == 47.6062
    assert p1.lon == -122.3321
    assert p1.alt == 100.5
    assert p1.timestamp == datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert p1.speed == 45.5
    
    p2 = points[1]
    assert p2.lat == 47.6100
    assert p2.timestamp == datetime(2023, 1, 1, 12, 1, 0, tzinfo=timezone.utc)
    assert p2.speed == 50.2
