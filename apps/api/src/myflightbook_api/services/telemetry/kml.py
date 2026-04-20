from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import List, Optional
import xml.etree.ElementTree as ET

from myflightbook_api.services.telemetry.base import TelemetryParserBase, TelemetryPoint

# Namespaces
NS_KML_22 = "http://www.opengis.net/kml/2.2"
NS_GX_22 = "http://www.google.com/kml/ext/2.2"
NS_KML_20_ALT = "http://earth.google.com/kml/2.0"
NS_KML_22_ALT = "http://earth.google.com/kml/2.2"
NS_KML_21_ALT = "http://earth.google.com/kml/2.1"

# Regex for KMLv1 coordinates: "(-?[0-9.]+) *, *(-?[0-9.]+)(?: *, *(-?[0-9]+))? *"
COORD_V1_REGEX = re.compile(r"(-?[0-9.]+) *, *(-?[0-9.]+)(?: *, *(-?[0-9.]+))? *")

class KMLParser(TelemetryParserBase):
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

        if "<kml" in data_str:
            try:
                ET.fromstring(data_str)
                return True
            except ET.ParseError:
                pass
                
        return False

    def parse(self, data: str | bytes) -> List[TelemetryPoint]:
        if isinstance(data, bytes):
            data_str = data.decode("utf-8")
        else:
            data_str = data
            
        try:
            root = ET.fromstring(data_str)
        except ET.ParseError as e:
            raise ValueError(f"Invalid KML XML: {e}")

        # Check for v2 (gx:Track)
        ns_kml = f"{{{NS_KML_22}}}"
        ns_gx = f"{{{NS_GX_22}}}"
        
        # We need to find Plackemark -> gx:Track, or just gx:Track
        gx_tracks = root.findall(f".//{ns_gx}Track")
        
        if gx_tracks:
            # Parse v2
            return self._parse_v2(root, gx_tracks[0], ns_kml, ns_gx)
            
        # Parse v1 (LineString -> coordinates)
        # Check standard and alt namespaces
        namespaces_to_check = [
            f"{{{NS_KML_22}}}",
            f"{{{NS_KML_20_ALT}}}",
            f"{{{NS_KML_21_ALT}}}",
            f"{{{NS_KML_22_ALT}}}",
        ]
        
        for ns in namespaces_to_check:
            # Try Placemark -> LineString -> coordinates
            placemarks = root.findall(f".//{ns}Placemark")
            coords_elems = []
            for pm in placemarks:
                for ls in pm.findall(f".//{ns}LineString"):
                    c = ls.find(f"{ns}coordinates")
                    if c is not None:
                        coords_elems.append(c)
            
            if coords_elems:
                return self._parse_v1_coords(coords_elems)
                
            # If not in Placemark, just find any LineString
            line_strings = root.findall(f".//{ns}LineString")
            if line_strings:
                return self._parse_v1_linestrings(line_strings, ns)

        raise ValueError("No valid KML track or LineString found.")

    def _parse_v1_coords(self, coords_elems: List[ET.Element]) -> List[TelemetryPoint]:
        coords_str = " ".join(e.text.replace("\r", " ").replace("\n", " ") for e in coords_elems if e.text)
        return self._extract_v1_points(coords_str)

    def _parse_v1_linestrings(self, line_strings: List[ET.Element], ns: str) -> List[TelemetryPoint]:
        coords_str = ""
        for ls in line_strings:
            c = ls.find(f"{ns}coordinates")
            if c is not None and c.text:
                coords_str += c.text.replace("\r", " ").replace("\n", " ") + " "
            elif ls.text: # Sometimes coords are directly in LineString? Legacy C# does e.Value
                coords_str += ls.text.replace("\r", " ").replace("\n", " ") + " "
                
        return self._extract_v1_points(coords_str)

    def _extract_v1_points(self, coords_str: str) -> List[TelemetryPoint]:
        points = []
        for match in COORD_V1_REGEX.finditer(coords_str):
            lon_str, lat_str, alt_str = match.groups()
            try:
                lon = float(lon_str)
                lat = float(lat_str)
                alt = float(alt_str) if alt_str else None
                points.append(TelemetryPoint(lat=lat, lon=lon, alt=alt))
            except ValueError:
                continue
                
        if not points:
            raise ValueError("No valid coordinates found in KML LineString.")
        return points

    def _parse_v2(self, root: ET.Element, track_elem: ET.Element, ns_kml: str, ns_gx: str) -> List[TelemetryPoint]:
        whens = track_elem.findall(f"{ns_kml}when")
        coords = track_elem.findall(f"{ns_gx}coord")
        
        points: List[TelemetryPoint] = []
        for i, coord in enumerate(coords):
            if not coord.text:
                continue
            parts = coord.text.replace(",", " ").split()
            if len(parts) < 2:
                continue
                
            try:
                lon = float(parts[0])
                lat = float(parts[1])
                alt = float(parts[2]) if len(parts) > 2 else None
            except ValueError:
                continue
                
            timestamp = None
            if i < len(whens) and whens[i].text:
                try:
                    ts_str = whens[i].text.strip().replace("Z", "+00:00")
                    timestamp = datetime.fromisoformat(ts_str)
                except ValueError:
                    pass
                    
            points.append(TelemetryPoint(lat=lat, lon=lon, alt=alt, timestamp=timestamp))

        # Extended data for speed (speedKts or speed_kts)
        has_speed = False
        simple_arrays = root.findall(f".//{ns_gx}SimpleArrayData")
        for arr in simple_arrays:
            name = arr.get("name", "").lower()
            if name in ("speedkts", "speed_kts"):
                vals = arr.findall(f".//{ns_gx}value")
                for i, v in enumerate(vals):
                    if i < len(points) and v.text:
                        try:
                            points[i].speed = float(v.text)
                            has_speed = True
                        except ValueError:
                            pass
                break
                
        # Derive speed if not present (parity with C#)
        if not has_speed:
            self._derive_speed(points)
            
        if not points:
            raise ValueError("No valid coordinates found in KML gx:Track.")
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
