from __future__ import annotations

import re
import math
from datetime import datetime, timezone
from typing import List, Optional
import xml.etree.ElementTree as ET

from myflightbook_api.services.telemetry.base import TelemetryParserBase, TelemetryPoint

# from .GPX.cs
# regex "^<gpx [^>]*xmlns[:=]"
# Namespaces
TOPOGRAFIX_10 = "http://www.topografix.com/GPX/1/0"
TOPOGRAFIX_11 = "http://www.topografix.com/GPX/1/1"
BAD_ELF = "http://bad-elf.com/xmlschemas/GpxExtensionsV1"

GPX_REGEX = re.compile(r"^<gpx [^>]*xmlns[:=]", re.MULTILINE)

class GPXParser(TelemetryParserBase):
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

        if GPX_REGEX.search(data_str):
            return True
            
        if "<gpx" in data_str:
            try:
                ET.fromstring(data_str)
                return True
            except ET.ParseError:
                return False
                
        return False

    def _get_namespace(self, root: ET.Element) -> str:
        # Determine the namespace from the root element tag
        match = re.match(r'\{.*\}', root.tag)
        return match.group(0) if match else ""

    def _find_speed(self, coord: ET.Element, ns: str) -> Optional[float]:
        # <speed>
        speed_elem = coord.find(f"{ns}speed")
        if speed_elem is not None and speed_elem.text:
            try:
                return float(speed_elem.text)
            except ValueError:
                pass
                
        # <extensions><speed> (BadElf)
        ext_elem = coord.find(f"{ns}extensions")
        if ext_elem is not None:
            bad_elf_ns = f"{{{BAD_ELF}}}"
            be_speed = ext_elem.find(f"{bad_elf_ns}speed")
            if be_speed is not None and be_speed.text:
                try:
                    return float(be_speed.text)
                except ValueError:
                    pass
                    
        return None

    def parse(self, data: str | bytes) -> List[TelemetryPoint]:
        if isinstance(data, bytes):
            data_str = data.decode("utf-8")
        else:
            data_str = data
            
        try:
            root = ET.fromstring(data_str)
        except ET.ParseError as e:
            raise ValueError(f"Invalid GPX XML: {e}")

        ns = self._get_namespace(root)
        
        # In C# parser: root.elements = xml.Descendants(ns + "trk").First().Descendants(ns + "trkseg")
        # Then for each element in root.elements, it gets Descendants(ns + "trkpt")
        # Let's find all trkpt elements across all trkseg inside trk.
        
        points: List[TelemetryPoint] = []
        
        for trk in root.findall(f".//{ns}trk"):
            for trkseg in trk.findall(f".//{ns}trkseg"):
                for coord in trkseg.findall(f".//{ns}trkpt"):
                    lat_str = coord.get("lat")
                    lon_str = coord.get("lon")
                    
                    if not lat_str or not lon_str:
                        continue
                        
                    try:
                        lat = float(lat_str)
                        lon = float(lon_str)
                    except ValueError:
                        continue
                        
                    alt: Optional[float] = None
                    ele_elem = coord.find(f"{ns}ele")
                    if ele_elem is not None and ele_elem.text:
                        try:
                            alt = float(ele_elem.text)
                        except ValueError:
                            pass
                            
                    timestamp: Optional[datetime] = None
                    time_elem = coord.find(f"{ns}time")
                    if time_elem is not None and time_elem.text:
                        try:
                            # C# uses ParseUTCDate(). We'll parse standard ISO8601 UTC
                            # Example: 2010-01-01T00:00:00Z
                            ts_str = time_elem.text.strip().replace("Z", "+00:00")
                            timestamp = datetime.fromisoformat(ts_str)
                        except ValueError:
                            pass
                            
                    speed = self._find_speed(coord, ns)
                    
                    points.append(TelemetryPoint(
                        lat=lat,
                        lon=lon,
                        alt=alt,
                        timestamp=timestamp,
                        speed=speed
                    ))
                    
        # In C# it derives speed if none is present: Position.DeriveSpeed(lst)
        # For parity, we will implement derive_speed later if the list has timestamps but no speeds.
        self._derive_speed(points)
                    
        if not points:
            raise ValueError("No valid track points found in GPX.")
            
        return points

    def _derive_speed(self, points: List[TelemetryPoint]) -> None:
        # C# DeriveSpeed algorithm
        # Checks if ANY speed exists. If not, it derives. Wait, C# says:
        # `if (!fHasSpeed) Position.DeriveSpeed(lst);`
        # meaning if NO speed was parsed across the entire file.
        has_speed = any(p.speed is not None for p in points)
        if has_speed:
            return
            
        if not points:
            return
            
        # Simplistic derive speed from C#:
        # Calculates NM distance / hours for segments with timestamps
        # We will implement this to match C# logic:
        
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
                    dist_in_nm = self._distance_nm(samp_ref.lat, samp_ref.lon, samp.lat, samp.lon)
                    if time_in_hours > 0:
                        speed_last = dist_in_nm / time_in_hours
                        samp.speed = speed_last
                    else:
                        samp.speed = speed_last

    def _distance_nm(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        # Haversine or simple great circle matching C# `LatLong.DistanceFrom`
        # C# DistanceFrom uses Math.Acos(Math.Sin(lat1)*Math.Sin(lat2) + Math.Cos(lat1)*Math.Cos(lat2)*Math.Cos(lon1-lon2)) * 3437.74677
        # with radians.
        rlat1 = math.radians(lat1)
        rlon1 = math.radians(lon1)
        rlat2 = math.radians(lat2)
        rlon2 = math.radians(lon2)
        
        val = math.sin(rlat1) * math.sin(rlat2) + math.cos(rlat1) * math.cos(rlat2) * math.cos(rlon1 - rlon2)
        # Clip to [-1, 1] to avoid domain errors from float precision
        val = max(min(val, 1.0), -1.0)
        
        rads = math.acos(val)
        return rads * 3437.74677 # NM conversion factor in MyFlightbook
