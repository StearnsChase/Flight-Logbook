from __future__ import annotations

import math
from datetime import datetime, timezone, timedelta

class Solar:
    @staticmethod
    def rad_to_deg(angle_rad: float) -> float:
        return 180.0 * angle_rad / math.pi

    @staticmethod
    def deg_to_rad(angle_deg: float) -> float:
        return math.pi * angle_deg / 180.0

    @staticmethod
    def calc_jd(year: int, month: int, day: int) -> float:
        if month <= 2:
            year -= 1
            month += 12
        
        a = math.floor(year / 100.0)
        b = 2 - a + math.floor(a / 4.0)

        jd = math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + b - 1524.5
        return jd

    @staticmethod
    def calc_time_julian_cent(jd: float) -> float:
        return (jd - 2451545.0) / 36525.0

    @staticmethod
    def calc_jd_from_julian_cent(t: float) -> float:
        return t * 36525.0 + 2451545.0

    @staticmethod
    def calc_geom_mean_long_sun(t: float) -> float:
        l0 = 280.46646 + t * (36000.76983 + 0.0003032 * t)
        while l0 > 360.0:
            l0 -= 360.0
        while l0 < 0.0:
            l0 += 360.0
        return l0

    @staticmethod
    def calc_geom_mean_anomaly_sun(t: float) -> float:
        return 357.52911 + t * (35999.05029 - 0.0001537 * t)

    @staticmethod
    def calc_eccentricity_earth_orbit(t: float) -> float:
        return 0.016708634 - t * (0.000042037 + 0.0000001267 * t)

    @staticmethod
    def calc_sun_eq_of_center(t: float) -> float:
        m = Solar.calc_geom_mean_anomaly_sun(t)
        mrad = Solar.deg_to_rad(m)
        sinm = math.sin(mrad)
        sin2m = math.sin(mrad + mrad)
        sin3m = math.sin(mrad + mrad + mrad)

        c = sinm * (1.914602 - t * (0.004817 + 0.000014 * t)) + sin2m * (0.019993 - 0.000101 * t) + sin3m * 0.000289
        return c

    @staticmethod
    def calc_sun_true_long(t: float) -> float:
        l0 = Solar.calc_geom_mean_long_sun(t)
        c = Solar.calc_sun_eq_of_center(t)
        return l0 + c

    @staticmethod
    def calc_sun_apparent_long(t: float) -> float:
        o = Solar.calc_sun_true_long(t)
        omega = 125.04 - 1934.136 * t
        lambda_ = o - 0.00569 - 0.00478 * math.sin(Solar.deg_to_rad(omega))
        return lambda_

    @staticmethod
    def calc_mean_obliquity_of_ecliptic(t: float) -> float:
        seconds = 21.448 - t * (46.8150 + t * (0.00059 - t * (0.001813)))
        e0 = 23.0 + (26.0 + (seconds / 60.0)) / 60.0
        return e0

    @staticmethod
    def calc_obliquity_correction(t: float) -> float:
        e0 = Solar.calc_mean_obliquity_of_ecliptic(t)
        omega = 125.04 - 1934.136 * t
        e = e0 + 0.00256 * math.cos(Solar.deg_to_rad(omega))
        return e

    @staticmethod
    def calc_sun_declination(t: float) -> float:
        e = Solar.calc_obliquity_correction(t)
        lambda_ = Solar.calc_sun_apparent_long(t)

        sint = math.sin(Solar.deg_to_rad(e)) * math.sin(Solar.deg_to_rad(lambda_))
        theta = Solar.rad_to_deg(math.asin(sint))
        return theta

    @staticmethod
    def calc_equation_of_time(t: float) -> float:
        epsilon = Solar.calc_obliquity_correction(t)
        l0 = Solar.calc_geom_mean_long_sun(t)
        e = Solar.calc_eccentricity_earth_orbit(t)
        m = Solar.calc_geom_mean_anomaly_sun(t)

        y = math.tan(Solar.deg_to_rad(epsilon) / 2.0)
        y *= y

        sin2l0 = math.sin(2.0 * Solar.deg_to_rad(l0))
        sinm = math.sin(Solar.deg_to_rad(m))
        cos2l0 = math.cos(2.0 * Solar.deg_to_rad(l0))
        sin4l0 = math.sin(4.0 * Solar.deg_to_rad(l0))
        sin2m = math.sin(2.0 * Solar.deg_to_rad(m))

        etime = y * sin2l0 - 2.0 * e * sinm + 4.0 * e * y * sinm * cos2l0 - 0.5 * y * y * sin4l0 - 1.25 * e * e * sin2m

        return Solar.rad_to_deg(etime) * 4.0

    @staticmethod
    def calc_hour_angle_sunrise(lat: float, solar_dec: float) -> float:
        lat_rad = Solar.deg_to_rad(lat)
        sd_rad = Solar.deg_to_rad(solar_dec)

        # 90.833 deg is the official NOAA standard for sunrise
        val = math.cos(Solar.deg_to_rad(90.833)) / (math.cos(lat_rad) * math.cos(sd_rad)) - math.tan(lat_rad) * math.tan(sd_rad)
        val = max(min(val, 1.0), -1.0)
        return math.acos(val)

    @staticmethod
    def calc_hour_angle_sunset(lat: float, solar_dec: float) -> float:
        lat_rad = Solar.deg_to_rad(lat)
        sd_rad = Solar.deg_to_rad(solar_dec)

        val = math.cos(Solar.deg_to_rad(90.833)) / (math.cos(lat_rad) * math.cos(sd_rad)) - math.tan(lat_rad) * math.tan(sd_rad)
        val = max(min(val, 1.0), -1.0)
        return -math.acos(val)

    @staticmethod
    def calc_sol_noon_utc(t: float, longitude: float) -> float:
        tnoon = Solar.calc_time_julian_cent(Solar.calc_jd_from_julian_cent(t) + longitude / 360.0)
        eq_time = Solar.calc_equation_of_time(tnoon)
        sol_noon_utc = 720 + (longitude * 4) - eq_time

        newt = Solar.calc_time_julian_cent(Solar.calc_jd_from_julian_cent(t) - 0.5 + sol_noon_utc / 1440.0)
        eq_time = Solar.calc_equation_of_time(newt)
        sol_noon_utc = 720 + (longitude * 4) - eq_time

        return sol_noon_utc

    @staticmethod
    def calc_sunrise_utc(jd: float, latitude: float, longitude: float) -> float:
        t = Solar.calc_time_julian_cent(jd)

        noonmin = Solar.calc_sol_noon_utc(t, longitude)
        tnoon = Solar.calc_time_julian_cent(jd + noonmin / 1440.0)

        eq_time = Solar.calc_equation_of_time(tnoon)
        solar_dec = Solar.calc_sun_declination(tnoon)
        hour_angle = Solar.calc_hour_angle_sunrise(latitude, solar_dec)

        delta = longitude - Solar.rad_to_deg(hour_angle)
        time_diff = 4 * delta
        time_utc = 720 + time_diff - eq_time

        newt = Solar.calc_time_julian_cent(Solar.calc_jd_from_julian_cent(t) + time_utc / 1440.0)
        eq_time = Solar.calc_equation_of_time(newt)
        solar_dec = Solar.calc_sun_declination(newt)
        hour_angle = Solar.calc_hour_angle_sunrise(latitude, solar_dec)
        delta = longitude - Solar.rad_to_deg(hour_angle)
        time_diff = 4 * delta
        time_utc = 720 + time_diff - eq_time

        return time_utc

    @staticmethod
    def calc_sunset_utc(jd: float, latitude: float, longitude: float) -> float:
        t = Solar.calc_time_julian_cent(jd)

        noonmin = Solar.calc_sol_noon_utc(t, longitude)
        tnoon = Solar.calc_time_julian_cent(jd + noonmin / 1440.0)

        eq_time = Solar.calc_equation_of_time(tnoon)
        solar_dec = Solar.calc_sun_declination(tnoon)
        hour_angle = Solar.calc_hour_angle_sunset(latitude, solar_dec)

        delta = longitude - Solar.rad_to_deg(hour_angle)
        time_diff = 4 * delta
        time_utc = 720 + time_diff - eq_time

        newt = Solar.calc_time_julian_cent(Solar.calc_jd_from_julian_cent(t) + time_utc / 1440.0)
        eq_time = Solar.calc_equation_of_time(newt)
        solar_dec = Solar.calc_sun_declination(newt)
        hour_angle = Solar.calc_hour_angle_sunset(latitude, solar_dec)

        delta = longitude - Solar.rad_to_deg(hour_angle)
        time_diff = 4 * delta
        time_utc = 720 + time_diff - eq_time

        return time_utc

    @staticmethod
    def calc_solar_angle(lat: float, lon: float, jd: float, minutes: float) -> float:
        julian_century = Solar.calc_time_julian_cent(jd + minutes / 1440.0)
        sun_declination_rad = Solar.deg_to_rad(Solar.calc_sun_declination(julian_century))
        lat_rad = Solar.deg_to_rad(lat)

        eq_of_time = Solar.calc_equation_of_time(julian_century)
        true_solar_time_min = (minutes + eq_of_time + 4 * lon) % 1440
        
        if true_solar_time_min / 4 < 0:
            hour_angle_deg = true_solar_time_min / 4 + 180
        else:
            hour_angle_deg = true_solar_time_min / 4 - 180
            
        val = math.sin(lat_rad) * math.sin(sun_declination_rad) + math.cos(lat_rad) * math.cos(sun_declination_rad) * math.cos(Solar.deg_to_rad(hour_angle_deg))
        val = max(min(val, 1.0), -1.0)
        zenith = Solar.rad_to_deg(math.acos(val))
        solar_elevation = 90 - zenith
        
        if solar_elevation > 85:
            atm_refraction_deg = 0.0
        elif solar_elevation > 5:
            atm_refraction_deg = 58.1 / math.tan(Solar.deg_to_rad(solar_elevation)) - 0.07 / math.pow(math.tan(Solar.deg_to_rad(solar_elevation)), 3) + 0.000086 / math.pow(math.tan(Solar.deg_to_rad(solar_elevation)), 5)
        elif solar_elevation > -0.575:
            atm_refraction_deg = 1735 + solar_elevation * (-518.2 + solar_elevation * (103.4 + solar_elevation * (-12.79 + solar_elevation * 0.711)))
        else:
            atm_refraction_deg = -20.772 / math.tan(Solar.deg_to_rad(solar_elevation))
            
        atm_refraction_deg /= 3600.0
        return solar_elevation + atm_refraction_deg


class SunriseSunsetTimes:
    def __init__(self, dt: datetime | None = None, latitude: float = 0.0, longitude: float = 0.0, night_flight_offset: int = 0):
        self.date: datetime = datetime.min.replace(tzinfo=timezone.utc)
        self.sunrise: datetime = datetime.min.replace(tzinfo=timezone.utc)
        self.sunset: datetime = datetime.min.replace(tzinfo=timezone.utc)
        self.latitude: float = latitude
        self.longitude: float = longitude
        self.night_landing_offset: int = 60
        self.night_flight_offset: int = night_flight_offset

        self.is_night: bool = False
        self.is_faa_night: bool = False
        self.is_within_night_offset: bool = False
        self.is_faa_civil_night: bool = False
        self.solar_angle: float = 0.0

        if dt:
            self.date = dt
            self._compute_times_at_location(dt)

    @staticmethod
    def _minutes_to_datetime(dt: datetime, minutes: float) -> datetime:
        dt_utc = datetime(dt.year, dt.month, dt.day, 0, 0, 0, tzinfo=timezone.utc)
        return dt_utc + timedelta(minutes=minutes)

    def _compute_times_at_location(self, dt: datetime) -> None:
        if self.latitude > 90 or self.latitude < -90:
            raise ValueError("Invalid Latitude")
        if self.longitude > 180 or self.longitude < -180:
            raise ValueError("Invalid Longitude")

        jd = Solar.calc_jd(dt.year, dt.month, dt.day)

        dt_utc = dt.astimezone(timezone.utc)
        self.solar_angle = Solar.calc_solar_angle(self.latitude, self.longitude, jd, dt_utc.hour * 60 + dt_utc.minute)
        self.is_faa_civil_night = self.solar_angle <= -6.0

        # NOAA algorithms use positive longitudes for WEST and negative for EAST.
        # The C# codebase passed `-longitude` because it uses standard (EAST positive).
        rise_time_gmt = Solar.calc_sunrise_utc(jd, self.latitude, -self.longitude)
        no_sunrise = math.isnan(rise_time_gmt)

        set_time_gmt = Solar.calc_sunset_utc(jd, self.latitude, -self.longitude)
        no_sunset = math.isnan(set_time_gmt)

        if not no_sunrise:
            self.sunrise = self._minutes_to_datetime(dt, rise_time_gmt)
        if not no_sunset:
            self.sunset = self._minutes_to_datetime(dt, set_time_gmt)

        self.is_night = self.is_faa_civil_night
        self.is_faa_night = False
        self.is_within_night_offset = False

        if self.sunrise <= dt <= self.sunset:
            # Daytime
            pass
        elif dt > self.sunset and not no_sunset:
            # Get next sunrise
            dt_tomorrow = dt + timedelta(days=1)
            jd_tomorrow = Solar.calc_jd(dt_tomorrow.year, dt_tomorrow.month, dt_tomorrow.day)
            next_sunrise = Solar.calc_sunrise_utc(jd_tomorrow, self.latitude, -self.longitude)
            if not math.isnan(next_sunrise):
                dt_next_sunrise = self._minutes_to_datetime(dt_tomorrow, next_sunrise)
                self.is_night = dt_next_sunrise > dt
                self.is_faa_night = (self.sunset + timedelta(minutes=self.night_landing_offset) <= dt) and (dt_next_sunrise - timedelta(minutes=self.night_landing_offset) >= dt)
                self.is_within_night_offset = (self.sunset + timedelta(minutes=self.night_flight_offset) <= dt) and (dt_next_sunrise - timedelta(minutes=self.night_flight_offset) >= dt)
        elif dt < self.sunrise and not no_sunrise:
            # Get previous sunset
            dt_yesterday = dt - timedelta(days=1)
            jd_yesterday = Solar.calc_jd(dt_yesterday.year, dt_yesterday.month, dt_yesterday.day)
            prev_sunset = Solar.calc_sunset_utc(jd_yesterday, self.latitude, -self.longitude)
            if not math.isnan(prev_sunset):
                dt_prev_sunset = self._minutes_to_datetime(dt_yesterday, prev_sunset)
                self.is_night = dt_prev_sunset < dt
                self.is_faa_night = (dt_prev_sunset + timedelta(minutes=self.night_landing_offset) <= dt) and (self.sunrise - timedelta(minutes=self.night_landing_offset) >= dt)
                self.is_within_night_offset = (dt_prev_sunset + timedelta(minutes=self.night_flight_offset) <= dt) and (self.sunrise - timedelta(minutes=self.night_flight_offset) >= dt)
