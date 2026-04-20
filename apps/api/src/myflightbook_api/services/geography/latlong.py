from __future__ import annotations

import math
import re
from typing import Any

from myflightbook_api.services.geography.dms_angle import DMSAngle, DisplayType, DMS_LATLONG

# Regexes from C#
REG_POSITION = re.compile(r"([NnSs]) ?(\d{1,2}) (\d{0,2}(?:\.\d*)?) ([EeWw]) ?(\d{1,3}) (\d{0,2}(?:\.\d*)?)")
REG_POSITION_TUPLE = re.compile(r"(?P<lat>-?\d{1,2}(?:\.\d*)?),(?P<lon>-?\d{1,3}(?:\.\d*)?)")

class LatLong:
    def __init__(self, lat: float | str | LatLong = 0.0, lon: float = 0.0):
        if isinstance(lat, LatLong):
            self.latitude = lat.latitude
            self.longitude = lat.longitude
        elif isinstance(lat, str):
            self._init_from_string(lat)
        else:
            self.latitude = float(lat)
            self.longitude = float(lon)

    def _init_from_string(self, sz_position: str) -> None:
        # e.g., "N 46 34.345 W 122 43.34"
        match = REG_POSITION.search(sz_position)
        if match:
            ns = match.group(1).upper()
            lat_deg = float(match.group(2))
            lat_min = float(match.group(3)) if match.group(3) else 0.0
            
            ew = match.group(4).upper()
            lon_deg = float(match.group(5))
            lon_min = float(match.group(6)) if match.group(6) else 0.0
            
            self.latitude = (-1 if ns == "S" else 1) * (lat_deg + (lat_min / 60.0))
            self.longitude = (-1 if ew == "W" else 1) * (lon_deg + (lon_min / 60.0))
            return
            
        # e.g., "47.6,-122.3"
        match = REG_POSITION_TUPLE.search(sz_position)
        if match:
            self.latitude = float(match.group("lat"))
            self.longitude = float(match.group("lon"))
            return
            
        raise ValueError(f"Bad position format: {sz_position}")

    @property
    def is_valid_latitude(self) -> bool:
        return -90.0 <= self.latitude <= 90.0

    @property
    def is_valid_longitude(self) -> bool:
        return -180.0 <= self.longitude <= 180.0

    @property
    def is_valid(self) -> bool:
        return self.is_valid_latitude and self.is_valid_longitude

    def is_same_location(self, other: LatLong | None, tolerance: float = 0.001) -> bool:
        if not other:
            return False
        return abs(other.latitude - self.latitude) < tolerance and abs(other.longitude - self.longitude) < tolerance

    @staticmethod
    def are_equal(ll1: LatLong | None, ll2: LatLong | None) -> bool:
        if ll1 and ll1.latitude == 0 and ll1.longitude == 0:
            ll1 = None
        if ll2 and ll2.latitude == 0 and ll2.longitude == 0:
            ll2 = None
            
        if ll1 is ll2 or (ll1 is None and ll2 is None):
            return True
            
        if (ll1 is None) ^ (ll2 is None):
            return False
            
        return ll1.is_same_location(ll2)

    @property
    def validation_error(self) -> str:
        if not self.is_valid_latitude:
            return "Invalid Latitude"
        if not self.is_valid_longitude:
            return "Invalid Longitude"
        return ""

    @property
    def latitude_string(self) -> str:
        return f"{self.latitude:.8f}"

    @property
    def longitude_string(self) -> str:
        return f"{self.longitude:.8f}"

    def __str__(self) -> str:
        return f"{self.latitude}, {self.longitude}"

    def to_deg_min_sec_string(self) -> str:
        lat_dms = DMSAngle(self.latitude)
        lon_dms = DMSAngle(self.longitude)
        return f"{lat_dms.to_string(DisplayType.LATITUDE)}, {lon_dms.to_string(DisplayType.LONGITUDE)}"

    def to_adhoc_fix_string(self) -> str:
        lat_dir = "N" if self.latitude > 0 else "S"
        lon_dir = "E" if self.longitude > 0 else "W"
        return f"@{abs(self.latitude):.8f}{lat_dir}{abs(self.longitude):.8f}{lon_dir}"

    @staticmethod
    def distance_between_points(ll1: LatLong, ll2: LatLong) -> float:
        if ll1.latitude == ll2.latitude and ll1.longitude == ll2.longitude:
            return 0.0
            
        if not ll1.is_valid or not ll2.is_valid:
            return float('nan')
            
        # Spherical calculation fallback from C#
        rlat1 = math.radians(ll1.latitude)
        rlon1 = math.radians(ll1.longitude)
        rlat2 = math.radians(ll2.latitude)
        rlon2 = math.radians(ll2.longitude)
        
        val = math.sin(rlat1) * math.sin(rlat2) + math.cos(rlat1) * math.cos(rlat2) * math.cos(rlon2 - rlon1)
        val = max(min(val, 1.0), -1.0)
        d = math.acos(val) * 3440.06479 # Radius of earth in NM approx
        return d if not math.isnan(d) else 0.0

    def distance_from(self, other: LatLong) -> float:
        return LatLong.distance_between_points(self, other)

    @staticmethod
    def try_parse(sz_lat: Any, sz_lon: Any) -> LatLong | None:
        try:
            return LatLong(float(sz_lat), float(sz_lon))
        except (ValueError, TypeError):
            return None

    def antipode(self) -> LatLong:
        new_lon = self.longitude - 180.0 if self.longitude > 0 else self.longitude + 180.0
        return LatLong(-self.latitude, new_lon)

def lat_lon_from_dms_string(sz: str) -> LatLong | None:
    match = DMS_LATLONG.search(sz)
    if match:
        lat_dms = DMSAngle(match.group(1))
        lon_dms = DMSAngle(match.group(2))
        return LatLong(lat_dms.value, lon_dms.value)
    # MGRS is ignored for now
    return None
