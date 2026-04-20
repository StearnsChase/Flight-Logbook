from __future__ import annotations

import re
from datetime import datetime, timezone, timedelta
from typing import List

from myflightbook_api.services.telemetry.base import TelemetryParserBase, TelemetryPoint

IGC_PREFIX_REGEX = re.compile(r"^A[a-zA-Z0-9]{6}[^,;]*$")
IGC_DATE_REGEX = re.compile(r"^HFDTE(?:DATE:)?(?P<day>[0-3][0-9])(?P<month>[01][0-9])(?P<year>[0-9]{2})", re.MULTILINE | re.IGNORECASE)
IGC_POSITION_REGEX = re.compile(r"^B(?P<hrs>[0-9]{2})(?P<min>[0-9]{2})(?P<sec>[0-9]{2})(?P<latd>[0-9]{2})(?P<latm>[0-9]{5})(?P<latns>[NS])(?P<lond>[0-9]{3})(?P<lonm>[0-9]{5})(?P<lonew>[EW])(?P<val>[AV])(?P<palt>[0-9]{5})(?P<gpsalt>[0-9]{5})", re.MULTILINE)

class IGCParser(TelemetryParserBase):
    def can_parse(self, data: str | bytes) -> bool:
        if isinstance(data, bytes):
            try:
                data_str = data.decode("utf-8")
            except UnicodeDecodeError:
                return False
        else:
            data_str = data
            
        if not data_str:
            return False

        first_line = data_str.split('\n', 1)[0].strip()
        if IGC_PREFIX_REGEX.match(first_line) and IGC_DATE_REGEX.search(data_str):
            return True
            
        return False

    def parse(self, data: str | bytes) -> List[TelemetryPoint]:
        if isinstance(data, bytes):
            data_str = data.decode("utf-8")
        else:
            data_str = data
            
        if not data_str:
            raise ValueError("No data to parse")
            
        if not self.can_parse(data_str):
            raise ValueError("Data to parse is not IGC format")
            
        date_match = IGC_DATE_REGEX.search(data_str)
        if not date_match:
            raise ValueError("IGC Data has no date field as required")
            
        day = int(date_match.group("day"))
        month = int(date_match.group("month"))
        year_2_digit = int(date_match.group("year"))
        
        # C# Logic for 2 digit year
        year_now = datetime.now(timezone.utc).year
        millenium = (year_now // 1000) * 1000
        year = year_2_digit + millenium
        if year > year_now:
            year -= 100
            
        dt_base = datetime(year, month, day, 0, 0, 0, tzinfo=timezone.utc)
        
        points: List[TelemetryPoint] = []
        
        # Note: The legacy C# parser calculates dayOffset but never uses it. 
        # For exact parity, we will just use h * 3600 + m * 60 + s
        
        for match in IGC_POSITION_REGEX.finditer(data_str):
            g = match.groupdict()
            h = int(g["hrs"])
            m = int(g["min"])
            s = int(g["sec"])
            
            latd = int(g["latd"])
            latm = int(g["latm"])
            latsign = -1 if g["latns"] == "S" else 1
            
            lond = int(g["lond"])
            lonm = int(g["lonm"])
            lonsign = -1 if g["lonew"] == "W" else 1
            
            has_alt = g["val"] == "A"
            palt = int(g["palt"])
            
            lat = latsign * (latd + latm / 60000.0)
            lon = lonsign * (lond + lonm / 60000.0)
            
            dt_sample = dt_base + timedelta(seconds=(h * 3600 + m * 60 + s))
            alt_sample = palt if has_alt else 0.0
            
            if lat != 0.0 and lon != 0.0:
                points.append(TelemetryPoint(lat=lat, lon=lon, alt=alt_sample, timestamp=dt_sample))
                
        # Derive speed
        self._derive_speed(points)
        
        return points

    def _derive_speed(self, points: List[TelemetryPoint]) -> None:
        # Same as GPX
        has_speed = any(p.speed is not None for p in points)
        if has_speed:
            return
            
        if not points:
            return
            
        import math
        
        def _distance_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
            rlat1 = math.radians(lat1)
            rlon1 = math.radians(lon1)
            rlat2 = math.radians(lat2)
            rlon2 = math.radians(lon2)
            val = math.sin(rlat1) * math.sin(rlat2) + math.cos(rlat1) * math.cos(rlat2) * math.cos(rlon1 - rlon2)
            val = max(min(val, 1.0), -1.0)
            return math.acos(val) * 3437.74677
        
        i_speed_ref = 0
        speed_last = 0.0
        min_refresh_seconds = 4.0
        
        for i_sample, samp in enumerate(points):
            if not samp.timestamp:
                continue
                
            for i_ref_new in range(i_speed_ref + 1, i_sample):
                samp_ref = points[i_ref_new]
                if not samp_ref.timestamp:
                    continue
                if (samp.timestamp - samp_ref.timestamp).total_seconds() > min_refresh_seconds:
                    i_speed_ref += 1
                    
            samp_ref = points[i_speed_ref]
            
            if i_sample <= i_speed_ref:
                samp.speed = speed_last
            else:
                if samp.timestamp and samp_ref.timestamp:
                    time_in_hours = (samp.timestamp - samp_ref.timestamp).total_seconds() / 3600.0
                    dist_in_nm = _distance_nm(samp_ref.lat, samp_ref.lon, samp.lat, samp.lon)
                    if time_in_hours > 0:
                        speed_last = dist_in_nm / time_in_hours
                        samp.speed = speed_last
                    else:
                        samp.speed = speed_last
