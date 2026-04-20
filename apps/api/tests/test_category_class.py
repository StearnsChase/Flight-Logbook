import pytest
from myflightbook_api.models.category_class import CatClassID

def test_catclassid_is_airplane():
    assert CatClassID.ASEL.is_airplane is True
    assert CatClassID.ASES.is_airplane is True
    assert CatClassID.AMEL.is_airplane is True
    assert CatClassID.HELICOPTER.is_airplane is False

def test_catclassid_is_powered():
    assert CatClassID.ASEL.is_powered is True
    assert CatClassID.HELICOPTER.is_powered is True
    assert CatClassID.GLIDER.is_powered is False
    assert CatClassID.HOT_AIR_BALLOON.is_powered is False

def test_catclassid_is_sea_class():
    assert CatClassID.ASES.is_sea_class is True
    assert CatClassID.ASEL.is_sea_class is False

def test_catclassid_has_engine():
    assert CatClassID.ASEL.has_engine is True
    assert CatClassID.GLIDER.has_engine is False
    assert CatClassID.GAS_BALLOON.has_engine is False
    assert CatClassID.HELICOPTER.has_engine is True

def test_catclassid_has_icao():
    assert CatClassID.ASEL.has_icao is True
    assert CatClassID.GLIDER.has_icao is False
