import pytest
import math
from myflightbook_api.services.geography.latlong import LatLong, lat_lon_from_dms_string
from myflightbook_api.services.geography.dms_angle import DMSAngle, DisplayType

def test_dms_angle_from_float():
    dms = DMSAngle(47.6062)
    assert dms.degrees == 47
    assert dms.minutes == 36
    # 0.6062 * 60 = 36.372
    # 0.372 * 60 = 22.32
    assert round(dms.seconds, 2) == 22.32
    assert dms.sign == 1
    
    dms_neg = DMSAngle(-122.3321)
    assert dms_neg.degrees == 122
    assert dms_neg.minutes == 19
    assert round(dms_neg.seconds, 2) == 55.56
    assert dms_neg.sign == -1

def test_dms_angle_from_string():
    # DMSNumeric
    dms = DMSAngle("22 03' 26.123\"S")
    assert dms.degrees == 22
    assert dms.minutes == 3
    assert dms.seconds == 26.123
    assert dms.sign == -1
    assert round(dms.value, 6) == -22.057256

    # DMSDecimal
    dms2 = DMSAngle("22.5483 S")
    assert round(dms2.value, 4) == -22.5483
    
    # DMSDotted
    dms3 = DMSAngle("W122.23.15")
    assert dms3.degrees == 122
    assert dms3.minutes == 23
    assert dms3.seconds == 15
    assert dms3.sign == -1

def test_latlong_distance():
    # KSEA to KPDX roughly
    ll1 = LatLong(47.4490, -122.3093)
    ll2 = LatLong(45.5887, -122.5975)
    
    dist = ll1.distance_from(ll2)
    # distance should be around 112 NM
    assert 111 < dist < 113

def test_latlong_parsing():
    ll = LatLong("N 46 34.345 W 122 43.34")
    assert round(ll.latitude, 6) == 46.572417
    assert round(ll.longitude, 6) == -122.722333
    
    ll2 = LatLong("47.6,-122.3")
    assert ll2.latitude == 47.6
    assert ll2.longitude == -122.3

def test_latlong_formatting():
    ll = LatLong(47.6062, -122.3321)
    assert ll.to_adhoc_fix_string() == "@47.60620000N122.33210000W"
