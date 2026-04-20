from __future__ import annotations

import csv
import io
import re
from datetime import datetime, timezone, timedelta
from typing import List

from myflightbook_api.services.telemetry.base import TelemetryParserBase, TelemetryPoint

BAJU_COPYRIGHT_REGEX = re.compile(r"Copyright.*BajuSoftware", re.MULTILINE)
BAJU_DATE_REGEX = re.compile(r"Date/Time: (?P<datestring>[0-9-/]+ .*[AP]M)", re.IGNORECASE | re.MULTILINE)

class BajuParser(TelemetryParserBase):
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

        return bool(BAJU_COPYRIGHT_REGEX.search(data_str))

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
            
        date_match = BAJU_DATE_REGEX.search(data_str)
        if not date_match:
            raise ValueError("Baju CSV missing Date/Time field")
            
        date_str = date_match.group("datestring")
        
        try:
            # Common parse format e.g. '1/1/2023 12:00:00 PM'
            # We don't have exact timezone mapping without GeoTimeZone so we parse as naive or assume UTC.
            dt_base = datetime.strptime(date_str, "%m/%d/%Y %I:%M:%S %p").replace(tzinfo=timezone.utc)
        except ValueError:
            raise ValueError(f"Could not parse base date {date_str}")
            
        # Parse CSV
        points: List[TelemetryPoint] = []
        
        f = io.StringIO(data_str)
        reader = csv.reader(f)
        
        headers = []
        for row in reader:
            if not row or len(row) < 4:
                continue
            headers = [h.strip() for h in row]
            break
            
        if not headers:
            raise ValueError("No valid CSV header row found")
            
        lat_idx = -1
        lon_idx = -1
        alt_idx = -1
        speed_idx = -1
        elapsed_sec_idx = -1
        
        for i, h in enumerate(headers):
            h_upper = h.upper()
            if h_upper == "LATITUDE":
                lat_idx = i
            elif h_upper == "LONGITUDE":
                lon_idx = i
            elif h_upper == "ALTITUDE (FEET IND)":
                alt_idx = i
            elif h_upper == "AIRSPEED (KNOTS IND)":
                speed_idx = i
            elif h_upper == "ELAPSEDSECONDS":
                elapsed_sec_idx = i
                
        if elapsed_sec_idx == -1:
            # Maybe parsing failed if columns are different
            pass
            
        for row in reader:
            if not "".join(row).strip():
                continue
                
            if len(row) <= max(lat_idx, lon_idx):
                continue
                
            try:
                lat = float(row[lat_idx]) if lat_idx != -1 else 0.0
                lon = float(row[lon_idx]) if lon_idx != -1 else 0.0
            except ValueError:
                continue
                
            if lat == 0.0 and lon == 0.0:
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
                    
            timestamp = dt_base
            if elapsed_sec_idx != -1 and len(row) > elapsed_sec_idx and row[elapsed_sec_idx]:
                try:
                    seconds = int(row[elapsed_sec_idx])
                    timestamp = dt_base + timedelta(seconds=seconds)
                except ValueError:
                    pass
                    
            points.append(TelemetryPoint(lat=lat, lon=lon, alt=alt, speed=speed, timestamp=timestamp))
            
        return points
