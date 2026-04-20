from __future__ import annotations

import csv
import io
import re
from datetime import datetime, timezone
from typing import List

from myflightbook_api.services.telemetry.base import TelemetryParserBase, TelemetryPoint

GARMIN_LOG_REGEX = re.compile(r"^(?P<line1>#airframe_info,.*)\n?(?P<header1>.+)\n?(?P<header2>.+)\n?", re.IGNORECASE | re.MULTILINE)
BROKEN_TELEMETRY_HEADER_REGEX = re.compile(r"^LAT,LON,PALT,SPEED,HERROR,DATE,COMMENT[\r\n]+[0-9]{1,2},[0-9]+,[0-9]{1,3},[0-9]+,[0-9]+,[0-9]+,[0-9],[0-9]+,[0-9],.*,.*[\r\n]")

class CSVTelemetryParser(TelemetryParserBase):
    def can_parse(self, data: str | bytes) -> bool:
        return data is not None

    def parse(self, data: str | bytes) -> List[TelemetryPoint]:
        if isinstance(data, bytes):
            try:
                data_str = data.decode("utf-8")
            except UnicodeDecodeError:
                raise ValueError("Data to parse is not valid UTF-8 CSV")
        else:
            data_str = data
            
        if not data_str:
            raise ValueError("No data to parse")
            
        fixed_data = self._fixed_flight_data(data_str)
        
        points: List[TelemetryPoint] = []
        
        # Read the fixed CSV data
        f = io.StringIO(fixed_data)
        reader = csv.reader(f)
        
        headers = []
        for row in reader:
            if not row or len(row) < 2 or row[0].startswith("#") or "Date (yyyy-mm-dd)" in row[0]:
                continue
            headers = [h.strip().upper() for h in row]
            break
            
        if not headers:
            raise ValueError("No valid CSV header row found")
            
        # Map columns
        lat_idx = -1
        lon_idx = -1
        alt_idx = -1
        speed_idx = -1
        
        date_idx = -1
        time_idx = -1
        utc_date_idx = -1
        utc_time_idx = -1
        datetime_idx = -1
        unix_ts_idx = -1
        tz_offset_idx = -1
        
        for i, h in enumerate(headers):
            # Hack for JPI date
            if h == "DATE" and "TIME" in headers:
                h = "LOCAL DATE"
            elif h == "TIME" and "DATE" in headers:
                h = "LOCAL TIME"
                
            if h in ("LAT", "LATITUDE"): lat_idx = i
            elif h in ("LON", "LONGITUDE"): lon_idx = i
            elif h in ("ALT", "PALT", "ALTGPS", "PRESSURE ALTITUDE"): alt_idx = i
            elif h in ("SPEED", "GND SPEED", "COMPUTEDSPEED"): speed_idx = i
            elif h in ("DATE", "NAKEDDATE", "LOCAL DATE"): date_idx = i
            elif h in ("TIME", "NAKEDTIME", "LOCAL TIME"): time_idx = i
            elif h in ("UTC DATE",): utc_date_idx = i
            elif h in ("UTC TIME",): utc_time_idx = i
            elif h in ("UTC DATETIME",): datetime_idx = i
            elif h in ("UNIXTIMESTAMP",): unix_ts_idx = i
            elif h in ("TZOFFSET", "UTC OFFSET"): tz_offset_idx = i

        if lat_idx == -1 or lon_idx == -1:
            raise ValueError("CSV must contain LAT and LON columns")
            
        for row in reader:
            if not "".join(row).strip():
                continue
                
            row = self._fix_row_hack(row, headers)
            
            if len(row) <= max(lat_idx, lon_idx):
                continue
                
            try:
                lat = float(row[lat_idx])
                lon = float(row[lon_idx])
            except ValueError:
                continue
                
            alt = None
            if alt_idx != -1 and len(row) > alt_idx and row[alt_idx]:
                try:
                    alt = float(row[alt_idx])
                except ValueError:
                    pass
                    
            speed = None
            if speed_idx != -1 and len(row) > speed_idx and row[speed_idx]:
                try:
                    speed = float(row[speed_idx])
                except ValueError:
                    pass
                    
            timestamp = self._parse_timestamp(
                row, date_idx, time_idx, utc_date_idx, utc_time_idx, datetime_idx, unix_ts_idx, tz_offset_idx
            )
            
            points.append(TelemetryPoint(lat=lat, lon=lon, alt=alt, speed=speed, timestamp=timestamp))
            
        has_speed = any(p.speed is not None for p in points)
        if not has_speed:
            self._derive_speed(points)
            
        return points

    def _parse_timestamp(
        self, row: List[str], date_idx: int, time_idx: int, utc_date_idx: int, utc_time_idx: int, 
        datetime_idx: int, unix_ts_idx: int, tz_offset_idx: int
    ) -> datetime | None:
        # Tries to reconstruct the timestamp based on C# logic
        if datetime_idx != -1 and len(row) > datetime_idx and row[datetime_idx]:
            try:
                # Assuming ISO 8601 UTC
                return datetime.fromisoformat(row[datetime_idx].replace("Z", "+00:00"))
            except ValueError:
                pass
                
        if unix_ts_idx != -1 and len(row) > unix_ts_idx and row[unix_ts_idx]:
            try:
                # Can be seconds or ms? C# says "ms since Jan 1 1970" but divides by 1000? Wait, it says "UnixTimeStamp, at least in ForeFlight, is # of ms since Jan 1 1970."
                ts = float(row[unix_ts_idx])
                if ts > 20000000000: # heuristic for ms vs seconds
                    ts = ts / 1000.0
                return datetime.fromtimestamp(ts, tz=timezone.utc)
            except ValueError:
                pass
                
        # Naked date / time combinations
        dt_val = None
        d_str = ""
        t_str = ""
        is_utc = False
        
        if utc_date_idx != -1 and len(row) > utc_date_idx and row[utc_date_idx]:
            d_str = row[utc_date_idx]
            is_utc = True
        elif date_idx != -1 and len(row) > date_idx and row[date_idx]:
            d_str = row[date_idx]
            
        if utc_time_idx != -1 and len(row) > utc_time_idx and row[utc_time_idx]:
            t_str = row[utc_time_idx]
            is_utc = True
        elif time_idx != -1 and len(row) > time_idx and row[time_idx]:
            t_str = row[time_idx]

        if d_str:
            try:
                if t_str:
                    # Combine date and time.
                    # Date formats vary wildly. We'll try common ISO subset
                    # Since MyFlightbook typically formats as yyyy-MM-dd
                    # and time as hh:mm:ss
                    d = datetime.fromisoformat(d_str.split("T")[0])
                    
                    # Custom time parse "hh:mm[:ss]"
                    t_parts = t_str.split(":")
                    h = int(t_parts[0])
                    m = int(t_parts[1])
                    s = int(t_parts[2]) if len(t_parts) > 2 else 0
                    
                    dt_val = datetime(d.year, d.month, d.day, h, m, s, tzinfo=timezone.utc)
                else:
                    d = datetime.fromisoformat(d_str.split("T")[0])
                    dt_val = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
            except ValueError:
                pass

        if dt_val and not is_utc and tz_offset_idx != -1 and len(row) > tz_offset_idx and row[tz_offset_idx]:
            try:
                # tzoffset can be in hours/minutes "hh:mm" or integer minutes
                tz_str = row[tz_offset_idx]
                if ":" in tz_str:
                    parts = tz_str.split(":")
                    mult = -1 if parts[0].startswith("-") else 1
                    mins = int(parts[0].replace("-", "")) * 60 + int(parts[1])
                    dt_val = dt_val + datetime.timedelta(minutes=mult * mins)
                else:
                    mins = int(tz_str)
                    dt_val = dt_val + datetime.timedelta(minutes=mins)
            except ValueError:
                pass
                
        return dt_val

    def _fixed_flight_data(self, flight_data: str) -> str:
        if not BROKEN_TELEMETRY_HEADER_REGEX.search(flight_data):
            return self._fixed_garmin_data(flight_data)
            
        lines = flight_data.splitlines()
        if not lines: return flight_data
        
        headers = lines[0]
        new_lines = [headers]
        
        for line in lines[1:]:
            row = line.split(",")
            if len(row) != 11:
                return flight_data
            # LAT,LON,PALT,SPEED,HERROR,DATE,COMMENT
            # Reconstruct
            new_row = [
                f"{row[0]}.{row[1]}",
                f"{row[2]}.{row[3]}",
                row[4],
                f"{row[5]}.{row[6]}",
                f"{row[7]}.{row[8]}",
                f'"{row[9]}"',
                f'"{row[10]}"'
            ]
            new_lines.append(",".join(new_row))
            
        return "\n".join(new_lines) + "\n"

    def _fixed_garmin_data(self, flight_data: str) -> str:
        match = GARMIN_LOG_REGEX.search(flight_data)
        if not match:
            return flight_data
            
        header1 = match.group("header1")
        header2 = match.group("header2")
        
        if header1.startswith("#"):
            return flight_data[match.start("header2"):]
            
        h1_parts = header1.split(",")
        h2_parts = header2.split(",")
        
        if len(h1_parts) != len(h2_parts):
            return flight_data
            
        merged = [f"{h1_parts[i].strip()} {h2_parts[i].strip()}" for i in range(len(h1_parts))]
        merged_str = ",".join(merged)
        
        merged_str = merged_str.replace("Date (yyyy-mm-dd) Lcl Date", "UTC Date")
        merged_str = merged_str.replace("UTC Time (hh:mm:ss) UTC Time", "UTC Time")
        merged_str = merged_str.replace("Latitude (deg) Latitude", "LAT")
        merged_str = merged_str.replace("Longitude (deg) Longitude", "LON")
        merged_str = merged_str.replace("GPS Altitude (ft) AltGPS", "ALTGPS")
        merged_str = merged_str.replace("GPS Ground Speed (kt) GndSpd", "GND SPEED")
        merged_str = merged_str.replace("Magnetic Heading (deg) HDG", "HDG")
        merged_str = merged_str.replace("Indicated Airspeed (kt) IAS", "IAS")
        
        return flight_data[:match.start()] + merged_str + "\n" + flight_data[match.end():]

    def _fix_row_hack(self, row: List[str], headers: List[str]) -> List[str]:
        if len(headers) == 7 and len(row) == 11 and headers[0] == "LAT" and headers[6] == "COMMENT":
            new_row = [
                f"{row[0]}.{row[1]}",
                f"{row[2]}.{row[3]}",
                row[4],
                f"{row[5]}.{row[6]}",
                f"{row[7]}.{row[8]}",
                row[9],
                row[10]
            ]
            return new_row
        return row

    def _derive_speed(self, points: List[TelemetryPoint]) -> None:
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
