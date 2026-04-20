from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
import httpx
import re

# Same template as legacy C# ADDS.cs
AWC_METAR_URL = "https://aviationweather.gov/api/data/metar?ids={ids}&hours={hours}&format=xml"


class FlightCategory:
    NONE = "None"
    VFR = "VFR"
    MVFR = "MVFR"
    IFR = "IFR"
    LIFR = "LIFR"


@dataclass
class SkyCondition:
    sky_cover: str
    cloud_base_ft_agl: int | None = None
    
    @property
    def display(self) -> str:
        cover_map = {
            "CLR": "Clear",
            "FEW": "Few",
            "SCT": "Scattered",
            "BKN": "Broken",
            "OVC": "Overcast"
        }
        return cover_map.get(self.sky_cover.upper(), self.sky_cover)


@dataclass
class METAR:
    raw_text: str = ""
    station_id: str = ""
    observation_time: str = ""
    latitude: float | None = None
    longitude: float | None = None
    temp_c: float | None = None
    dewpoint_c: float | None = None
    wind_dir_degrees: str = ""
    wind_speed_kt: int | None = None
    wind_gust_kt: int | None = None
    visibility_statute_mi: str = ""
    altim_in_hg: float | None = None
    sea_level_pressure_mb: float | None = None
    quality_control_flags: dict[str, bool] = field(default_factory=dict)
    wx_string: str = ""
    sky_conditions: list[SkyCondition] = field(default_factory=list)
    flight_category: str = ""
    three_hr_pressure_tendency_mb: float | None = None
    max_t_c: float | None = None
    min_t_c: float | None = None
    precip_in: float | None = None
    metar_type: str = ""
    elevation_m: float | None = None
    
    @property
    def timestamp(self) -> datetime | None:
        if not self.observation_time:
            return None
        try:
            # typical format "2023-01-01T12:00:00Z"
            ts_str = self.observation_time.strip().replace("Z", "+00:00")
            return datetime.fromisoformat(ts_str)
        except ValueError:
            return None

    @property
    def category(self) -> str:
        cat = (self.flight_category or "").upper()
        if cat in ("VFR", "MVFR", "IFR", "LIFR"):
            return cat
        return FlightCategory.NONE

    @property
    def metar_type_display(self) -> str:
        mtype = (self.metar_type or "").upper()
        if mtype == "METAR":
            return ""
        if mtype == "SPECI":
            return "Special"
        return self.metar_type

    @property
    def time_display(self) -> str:
        ts = self.timestamp
        if ts:
            return ts.strftime("%m/%d/%Y %H:%M:%S (Zulu)")
        return ""

    @property
    def altitude_hg_display(self) -> str:
        return f"{self.altim_in_hg:.2f}" if self.altim_in_hg is not None else ""

    @property
    def visibility_display(self) -> str:
        return f"{self.visibility_statute_mi}" if self.visibility_statute_mi else ""

    @property
    def temp_display(self) -> str:
        return f"{self.temp_c:.1f}°C" if self.temp_c is not None else ""

    @property
    def dewpoint_display(self) -> str:
        return f"{self.dewpoint_c:.1f}°C" if self.dewpoint_c is not None else ""

    @property
    def temp_dewpoint_display(self) -> str:
        if self.temp_c is not None and self.dewpoint_c is not None:
            return f"Temp: {self.temp_c:.1f}°C Dewpoint: {self.dewpoint_c:.1f}°C"
        elif self.temp_c is not None:
            return f"Temp: {self.temp_c:.1f}°C"
        elif self.dewpoint_c is not None:
            return f"Dewpoint: {self.dewpoint_c:.1f}°C"
        return ""

    @property
    def temp_and_dewpoint_display(self) -> str:
        if self.dewpoint_c is not None:
            return f"{self.temp_display}/{self.dewpoint_display}"
        return self.temp_display

    @property
    def wind_dir_display(self) -> str:
        if self.wind_dir_degrees:
            try:
                wdir = int(self.wind_dir_degrees)
                return f"{wdir}°"
            except ValueError:
                return self.wind_dir_degrees
        return ""

    @property
    def color_for_flight_rules(self) -> str:
        color_map = {
            FlightCategory.NONE: "Black",
            FlightCategory.VFR: "Green",
            FlightCategory.MVFR: "Blue",
            FlightCategory.IFR: "Red",
            FlightCategory.LIFR: "Purple"
        }
        return color_map.get(self.category, "Black")


class ADDSService:
    @staticmethod
    async def get_metars_for_airports(airports: str, hour_lookback: int) -> list[METAR]:
        if not airports:
            return []

        # Issue #1020 mapping / filtering (legacy stripped non-navaid prefixes, but here we just take the requested)
        codes = [code.strip().upper() for code in re.split(r'[\s,;]+', airports) if code.strip()]
        
        # Typically AWC takes comma separated
        fixed_codes = ",".join(codes)
        url = AWC_METAR_URL.format(ids=fixed_codes, hours=hour_lookback)
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=10.0)
                resp.raise_for_status()
                return ADDSService._parse_awc_xml(resp.text)
        except Exception:
            return []

    @staticmethod
    async def latest_metars_for_airports(airports: str, one_per_station: bool = True) -> list[METAR]:
        hours = 3 if one_per_station else 24
        all_metars = await ADDSService.get_metars_for_airports(airports, hours)

        if not all_metars:
            return []

        # Sort by station_id asc, then by timestamp desc
        def sort_key(m: METAR):
            ts_val = m.timestamp.timestamp() if m.timestamp else 0.0
            return (m.station_id.upper(), -ts_val)

        all_metars.sort(key=sort_key)

        result = []
        seen_stations = set()

        for m in all_metars:
            station = m.station_id.upper()
            if station not in seen_stations:
                result.append(m)
                if one_per_station:
                    seen_stations.add(station)

        return result

    @staticmethod
    def _parse_awc_xml(xml_text: str) -> list[METAR]:
        metars = []
        try:
            root = ET.fromstring(xml_text)
            # The AWC XML typically puts data inside <data><METAR>...</METAR></data>
            data_node = root.find("data")
            if data_node is None:
                return []

            for metar_node in data_node.findall("METAR"):
                m = METAR()
                m.raw_text = getattr(metar_node.find("raw_text"), "text", "")
                m.station_id = getattr(metar_node.find("station_id"), "text", "")
                m.observation_time = getattr(metar_node.find("observation_time"), "text", "")
                
                lat_text = getattr(metar_node.find("latitude"), "text", None)
                if lat_text: m.latitude = float(lat_text)
                
                lon_text = getattr(metar_node.find("longitude"), "text", None)
                if lon_text: m.longitude = float(lon_text)

                temp_text = getattr(metar_node.find("temp_c"), "text", None)
                if temp_text: m.temp_c = float(temp_text)

                dewp_text = getattr(metar_node.find("dewpoint_c"), "text", None)
                if dewp_text: m.dewpoint_c = float(dewp_text)

                m.wind_dir_degrees = getattr(metar_node.find("wind_dir_degrees"), "text", "")
                
                wspd_text = getattr(metar_node.find("wind_speed_kt"), "text", None)
                if wspd_text: m.wind_speed_kt = int(wspd_text)
                
                wgust_text = getattr(metar_node.find("wind_gust_kt"), "text", None)
                if wgust_text: m.wind_gust_kt = int(wgust_text)

                m.visibility_statute_mi = getattr(metar_node.find("visibility_statute_mi"), "text", "")
                
                alt_text = getattr(metar_node.find("altim_in_hg"), "text", None)
                if alt_text: m.altim_in_hg = float(alt_text)

                slp_text = getattr(metar_node.find("sea_level_pressure_mb"), "text", None)
                if slp_text: m.sea_level_pressure_mb = float(slp_text)

                m.flight_category = getattr(metar_node.find("flight_category"), "text", "")
                m.wx_string = getattr(metar_node.find("wx_string"), "text", "")
                m.metar_type = getattr(metar_node.find("metar_type"), "text", "")

                for sky_node in metar_node.findall("sky_condition"):
                    cover = sky_node.get("sky_cover", "")
                    base = sky_node.get("cloud_base_ft_agl")
                    if cover:
                        m.sky_conditions.append(SkyCondition(
                            sky_cover=cover,
                            cloud_base_ft_agl=int(base) if base else None
                        ))

                qc_node = metar_node.find("quality_control_flags")
                if qc_node is not None:
                    for child in qc_node:
                        m.quality_control_flags[child.tag] = (child.text.upper() == "TRUE") if child.text else False

                metars.append(m)
        except ET.ParseError:
            pass

        return metars
