from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from myflightbook_api.services.telemetry.base import TelemetryParserBase, TelemetryPoint

class NMEAParser(TelemetryParserBase):
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

        return data_str.strip().upper().startswith("$GP")

    def parse(self, data: str | bytes) -> List[TelemetryPoint]:
        if isinstance(data, bytes):
            data_str = data.decode("utf-8")
        else:
            data_str = data
            
        if not data_str:
            raise ValueError("No data to parse")
            
        points: List[TelemetryPoint] = []
        
        lines = data_str.splitlines()
        alt: float = 0.0
        
        current_year = datetime.now(timezone.utc).year
        
        for idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            parts = line.split(",")
            
            try:
                if parts[0].upper() == "$GPGGA":
                    # parts[6] is Fix quality. 0 = invalid
                    if len(parts) > 9 and parts[6] != "0" and parts[9]:
                        # C# parser converts to feet:
                        # alt = Convert.ToDouble(rgWords[9], CultureInfo.InvariantCulture) * ConversionFactors.FeetPerMeter;
                        # However, AltitudeUnits says AltitudeUnitTypes.Meters. 
                        # Wait, C# code says `alt = Convert.ToDouble(rgWords[9]) * ConversionFactors.FeetPerMeter;`
                        # This means it's converting the meters to feet internally? 
                        # NMEA GGA gives altitude in METERS.
                        # Wait, let's check what AltitudeUnits returns: `get { return AltitudeUnitTypes.Meters; }`
                        # If C# returns Meters but stores it after * 3.28084 (FeetPerMeter)... that's weird.
                        # Let's just follow C# exactly. MyFlightbook.Geography.ConversionFactors.FeetPerMeter is 3.280839895
                        alt_meters = float(parts[9])
                        alt = alt_meters * 3.280839895013123 # FeetPerMeter
                        
                elif parts[0].upper() == "$GPRMC":
                    if len(parts) < 10:
                        continue
                        
                    time_str = parts[1] # HHMMSS
                    date_str = parts[9] # DDMMYY
                    
                    if len(time_str) < 6 or len(date_str) < 6:
                        continue
                        
                    year_2_digit = int(date_str[4:6])
                    year_20th = 1900 + year_2_digit
                    year_21st = 2000 + year_2_digit
                    
                    if abs(current_year - year_20th) < abs(current_year - year_21st):
                        year = year_20th
                    else:
                        year = year_21st
                        
                    month = int(date_str[2:4])
                    day = int(date_str[0:2])
                    
                    hour = int(time_str[0:2])
                    minute = int(time_str[2:4])
                    second = int(time_str[4:6])
                    
                    dt = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
                    
                    # Lat: 4807.038 -> 48 deg 07.038'
                    lat_str = parts[3]
                    lat_dir = parts[4].upper()
                    
                    if not lat_str:
                        continue
                    
                    lat_deg = float(lat_str[0:2])
                    lat_min = float(lat_str[2:])
                    lat = lat_deg + (lat_min / 60.0)
                    if lat_dir == "S":
                        lat = -lat
                        
                    # Lon: 01131.000 -> 11 deg 31.000'
                    lon_str = parts[5]
                    lon_dir = parts[6].upper()
                    
                    if not lon_str:
                        continue
                        
                    lon_deg = float(lon_str[0:3])
                    lon_min = float(lon_str[3:])
                    lon = lon_deg + (lon_min / 60.0)
                    if lon_dir == "W":
                        lon = -lon
                        
                    speed_kts = float(parts[7]) if parts[7] else 0.0
                    
                    points.append(TelemetryPoint(
                        lat=lat,
                        lon=lon,
                        alt=alt,
                        timestamp=dt,
                        speed=speed_kts
                    ))
                    
            except (ValueError, IndexError):
                # C# catches FormatException and IndexOutOfRangeException and sets fResult = false, 
                # but continues parsing other lines.
                continue
                
        return points
