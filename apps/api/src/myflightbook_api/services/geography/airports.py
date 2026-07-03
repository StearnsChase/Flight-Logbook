from __future__ import annotations

import math
import re
from typing import Sequence

from sqlalchemy import func, or_, select

from myflightbook_api.db.session import SessionLocal
from myflightbook_api.models.airport import Airport
from myflightbook_api.services.geography.latlong import LatLong, lat_lon_from_dms_string

# Minimum lengths for validation
MIN_NAVAID_CODE_LENGTH = 2
MIN_AIRPORT_CODE_LENGTH = 3
MAX_CODE_LENGTH = 6

FORCE_NAVAID_PREFIX = "@"
US_AIRPORT_PREFIX = "K"

# Regex for AdHoc and MGRS
REG_AD_HOC_FIX = re.compile(rf"{FORCE_NAVAID_PREFIX}\d{{1,2}}(?:[.,]\d*)?[NS]\d{{1,3}}(?:[.,]\d*)?[EW]\b")
REG_MGRS = re.compile(rf"{FORCE_NAVAID_PREFIX}\d{{1,2}}[^ABIOYZabioyz][A-Za-z]{{2}}([0-9][0-9])+\b")

# Regex to split a route string into individual airport/fix codes
# Matches adhoc fixes, mgrs fixes, forced navaids, or standard 2-6 letter codes
REG_AIRPORT_SPLIT = re.compile(
    rf"({REG_AD_HOC_FIX.pattern}|{REG_MGRS.pattern}|@[A-Z0-9]{{{min(MIN_NAVAID_CODE_LENGTH, MIN_AIRPORT_CODE_LENGTH)},{MAX_CODE_LENGTH}}}\b|\b[A-Z0-9]{{{min(MIN_NAVAID_CODE_LENGTH, MIN_AIRPORT_CODE_LENGTH)},{MAX_CODE_LENGTH}}}\b)",
    re.IGNORECASE
)


class RouteParser:
    @staticmethod
    def is_us_airport(code: str) -> bool:
        return bool(code and len(code) == 4 and code.upper().startswith(US_AIRPORT_PREFIX))

    @staticmethod
    def us_prefix_convenience_alias(code: str) -> str:
        if RouteParser.is_us_airport(code):
            return code[1:]
        return code

    @staticmethod
    def split_codes(route_string: str) -> list[str]:
        """
        Given a string of airport codes (e.g., "KSFO @LAX KPAE"), splits them into a list of codes.
        """
        if not route_string:
            return []
            
        matches = REG_AIRPORT_SPLIT.findall(route_string.upper())
        # Depending on regex capture groups, findall might return tuples if there are multiple groups
        # Since our split regex has an outer group, we'll extract the first element or the string itself
        codes = []
        for m in matches:
            if isinstance(m, tuple):
                codes.append(m[0])
            else:
                codes.append(m)
        return codes


class AdHocFix(Airport):
    """
    Represents an ad-hoc fix (e.g., @47.348N103.23W) rather than a database airport.
    """
    def __init__(self, dms_string: str):
        super().__init__()
        # Ensure we strip the prefix before parsing
        clean_dms = dms_string.replace(FORCE_NAVAID_PREFIX, "")
        
        ll = lat_lon_from_dms_string(clean_dms)
        if not ll:
            raise ValueError(f"Invalid AdHoc Fix format: {clean_dms}")
            
        self.code = dms_string
        self.latitude = ll.latitude
        self.longitude = ll.longitude
        self.facility_type = "FX"
        self.name = ll.to_deg_min_sec_string()


class AirportQueryService:
    @staticmethod
    async def airports_matching_codes(codes: Sequence[str]) -> list[Airport]:
        if not codes:
            return []

        airports: list[Airport] = []
        db_codes: list[str] = []

        for raw_code in codes:
            code = (raw_code or "").strip().upper()
            if not code:
                continue

            if REG_AD_HOC_FIX.fullmatch(code):
                airports.append(AdHocFix(code))
                continue

            if code.startswith(FORCE_NAVAID_PREFIX):
                db_codes.append(code[len(FORCE_NAVAID_PREFIX):])
                continue

            db_codes.append(code)
            alias = RouteParser.us_prefix_convenience_alias(code)
            if alias != code:
                db_codes.append(alias)

        if not db_codes:
            return airports

        deduped_codes = list(dict.fromkeys(db_codes))
        async with SessionLocal() as session:
            result = await session.execute(
                select(Airport)
                .where(Airport.code.in_(deduped_codes))
                .order_by(Airport.code.asc(), Airport.facility_type.asc())
            )
            airports.extend(result.scalars().all())

        return airports

    @staticmethod
    async def airports_near_position(lat: float, lon: float, limit: int = 10, include_heliports: bool = False) -> list[Airport]:
        location = LatLong(lat, lon)
        if not location.is_valid:
            return []

        min_lat = max(lat - 1.5, -90.0)
        max_lat = min(lat + 1.5, 90.0)
        min_lon = lon - 1.5
        max_lon = lon + 1.5

        wraps_dateline = False
        if min_lon < -180.0:
            min_lon += 360.0
            wraps_dateline = True
        if max_lon > 180.0:
            max_lon -= 360.0
            wraps_dateline = True

        facility_types = ["A", "S"]
        if include_heliports:
            facility_types.append("H")

        distance_expr = func.acos(
            func.sin(func.radians(Airport.latitude)) * func.sin(func.radians(lat))
            + func.cos(func.radians(Airport.latitude))
            * func.cos(func.radians(lat))
            * func.cos(func.radians(lon - Airport.longitude))
        ) * 3440.06479

        longitude_clause = (
            or_(Airport.longitude >= min_lon, Airport.longitude <= max_lon)
            if wraps_dateline
            else Airport.longitude.between(min_lon, max_lon)
        )

        async with SessionLocal() as session:
            result = await session.execute(
                select(Airport)
                .where(
                    Airport.latitude.between(min_lat, max_lat),
                    longitude_clause,
                    Airport.facility_type.in_(facility_types),
                )
                .order_by(distance_expr.asc(), func.length(Airport.code).desc())
                .limit(max(1, limit))
            )
            return list(result.scalars().all())

    @staticmethod
    async def airports_within_bounds(lat_south: float, lon_west: float, lat_north: float, lon_east: float) -> list[Airport]:
        south_west = LatLong(lat_south, lon_west)
        north_east = LatLong(lat_north, lon_east)
        if not south_west.is_valid or not north_east.is_valid:
            return []

        lat_height = abs(lat_north - lat_south)
        lon_width = lon_east - lon_west
        if lon_width < 0:
            lon_width += 360.0

        if lat_height > 5.0 or lon_width > 5.0:
            return []

        longitude_clause = (
            or_(Airport.longitude >= lon_west, Airport.longitude <= lon_east)
            if lon_east < lon_west
            else Airport.longitude.between(lon_west, lon_east)
        )

        async with SessionLocal() as session:
            result = await session.execute(
                select(Airport)
                .where(
                    Airport.latitude.between(lat_south, lat_north),
                    longitude_clause,
                    Airport.facility_type.in_(("A", "S")),
                )
                .order_by(Airport.code.asc())
                .limit(200)
            )
            return list(result.scalars().all())
