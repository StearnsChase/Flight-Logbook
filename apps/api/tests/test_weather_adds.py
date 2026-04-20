import pytest
from myflightbook_api.services.weather.adds import ADDSService, METAR, FlightCategory

MOCK_XML = """<?xml version="1.0" encoding="UTF-8"?>
<response xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.2">
  <data num_results="1">
    <METAR>
      <raw_text>KSEA 011200Z 18010KT 10SM BKN050 15/10 A2992 RMK AO2</raw_text>
      <station_id>KSEA</station_id>
      <observation_time>2023-01-01T12:00:00Z</observation_time>
      <latitude>47.45</latitude>
      <longitude>-122.31</longitude>
      <temp_c>15.0</temp_c>
      <dewpoint_c>10.0</dewpoint_c>
      <wind_dir_degrees>180</wind_dir_degrees>
      <wind_speed_kt>10</wind_speed_kt>
      <visibility_statute_mi>10.0</visibility_statute_mi>
      <altim_in_hg>29.917322</altim_in_hg>
      <sea_level_pressure_mb>1013.2</sea_level_pressure_mb>
      <quality_control_flags>
        <auto_station>TRUE</auto_station>
      </quality_control_flags>
      <sky_condition sky_cover="BKN" cloud_base_ft_agl="5000" />
      <flight_category>VFR</flight_category>
      <metar_type>METAR</metar_type>
      <elevation_m>112.0</elevation_m>
    </METAR>
  </data>
</response>
"""

def test_parse_awc_xml():
    metars = ADDSService._parse_awc_xml(MOCK_XML)
    
    assert len(metars) == 1
    m = metars[0]
    
    assert m.station_id == "KSEA"
    assert m.temp_c == 15.0
    assert m.dewpoint_c == 10.0
    assert m.wind_dir_degrees == "180"
    assert m.wind_speed_kt == 10
    assert m.visibility_statute_mi == "10.0"
    assert m.flight_category == "VFR"
    assert m.category == FlightCategory.VFR
    
    assert len(m.sky_conditions) == 1
    assert m.sky_conditions[0].sky_cover == "BKN"
    assert m.sky_conditions[0].cloud_base_ft_agl == 5000
    
    assert m.quality_control_flags.get("auto_station") is True

def test_metar_display_properties():
    m = METAR(
        station_id="KSEA",
        temp_c=15.2,
        dewpoint_c=10.1,
        wind_dir_degrees="180",
        flight_category="IFR",
        metar_type="SPECI"
    )
    
    assert m.temp_display == "15.2°C"
    assert m.dewpoint_display == "10.1°C"
    assert m.temp_and_dewpoint_display == "15.2°C/10.1°C"
    assert m.wind_dir_display == "180°"
    assert m.category == FlightCategory.IFR
    assert m.color_for_flight_rules == "Red"
    assert m.metar_type_display == "Special"
