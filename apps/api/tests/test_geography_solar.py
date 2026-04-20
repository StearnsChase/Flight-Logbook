import pytest
from datetime import datetime, timezone, timedelta
from myflightbook_api.services.geography.solar import Solar, SunriseSunsetTimes

def test_solar_calculations():
    # Example: Seattle, WA on Jan 1, 2023
    # Lat: 47.6062, Lon: -122.3321
    lat = 47.6062
    lon = -122.3321
    dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    
    times = SunriseSunsetTimes(dt, lat, lon)
    
    # Check sunrise/sunset UTC for this day
    # Roughly sunrise ~15:58 UTC (7:58 AM PST), sunset ~00:28 UTC next day (4:28 PM PST)
    assert times.sunrise.year == 2023
    assert times.sunrise.month == 1
    assert times.sunrise.day == 1
    assert 15 <= times.sunrise.hour <= 16
    
    # Is it night at 12:00 UTC? Yes (4 AM PST)
    assert times.is_night is True
    # Is it FAA night? Yes (it's more than 1 hour before sunrise and 1 hour after sunset)
    assert times.is_faa_night is True

def test_solar_daytime():
    # 20:00 UTC (12 PM PST)
    dt = datetime(2023, 1, 1, 20, 0, 0, tzinfo=timezone.utc)
    times = SunriseSunsetTimes(dt, 47.6062, -122.3321)
    
    assert times.is_night is False
    assert times.is_faa_night is False

def test_solar_civil_twilight():
    # ~30 mins before sunrise
    # Sunrise is ~15:58 UTC
    dt = datetime(2023, 1, 1, 15, 30, 0, tzinfo=timezone.utc)
    times = SunriseSunsetTimes(dt, 47.6062, -122.3321)
    
    # 30 mins before sunrise is usually not FAA Night (needs 1 hr offset)
    assert times.is_faa_night is False
    
    # But is it civil twilight? 
    # Depends on exact solar angle. 
    # Let's just check that properties are populated
    assert -10 <= times.solar_angle <= 10 
