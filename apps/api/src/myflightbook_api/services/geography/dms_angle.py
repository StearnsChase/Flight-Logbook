from __future__ import annotations

import enum
import math
import re

# Regexes from RegexUtility.cs
DMS_NUMERIC = re.compile(r"(\d{1,3})\D+([0-5]?\d)\D+(\d+\.?\d*)\D*([NEWS])", re.IGNORECASE)
DMS_DECIMAL = re.compile(r"(\d{0,3}([,.]\d+)?)\D*([NEWS])", re.IGNORECASE)
DMS_DOTTED = re.compile(r"([NEWSnews])[ .]?(\d{0,3})[ .]?(\d{0,2})[ .]?(\d{0,2})", re.IGNORECASE)
DMS_DEGREES = re.compile(r"-?(\d+)°(\d+([.,]\d+)?)", re.IGNORECASE)
DMS_LATLONG = re.compile(r"([^a-zA-Z]+[NS]) *([^a-zA-Z]+[EW])", re.IGNORECASE)


class DisplayType(enum.Enum):
    DECIMAL = "decimal"
    LATITUDE = "latitude"
    LONGITUDE = "longitude"


class DMSAngle:
    def __init__(self, angle_or_str: float | str):
        self.degrees: int = 0
        self.minutes: int = 0
        self.seconds: float = 0.0
        self.sign: int = 1

        if isinstance(angle_or_str, (int, float)):
            self._init_from_angle(float(angle_or_str))
        else:
            self._init_from_string(angle_or_str)

    def _init_from_angle(self, angle: float) -> None:
        self.sign = -1 if angle < 0 else 1
        angle = abs(angle)
        self.degrees = int(math.floor(angle))
        dmin = (angle - self.degrees) * 60.0
        self.minutes = int(math.floor(dmin))
        self.seconds = (dmin - self.minutes) * 60.0

    def _init_from_string(self, sz_angle: str) -> None:
        self.degrees = 0
        self.minutes = 0
        self.seconds = 0.0
        self.sign = 1

        if not sz_angle:
            return

        # DMSNumeric ("22 03' 26.123"S)
        match = DMS_NUMERIC.search(sz_angle)
        if match:
            self.degrees = int(match.group(1))
            self.minutes = int(match.group(2))
            self.seconds = float(match.group(3))
            direction = match.group(4).upper()
            self.sign = 1 if direction in ("N", "E") else -1
            return

        # DMSDecimal ("22.5483 S 27.863E") -> It only matches one part!
        match = DMS_DECIMAL.search(sz_angle)
        if match and match.group(1) and match.group(3):
            direction = match.group(3).upper()
            self.sign = 1 if direction in ("N", "E") else -1
            angle = float(match.group(1).replace(",", "."))
            self._init_from_angle(self.sign * abs(angle))
            return

        # DMSDotted ("W122.23.15")
        match = DMS_DOTTED.search(sz_angle)
        if match:
            direction = match.group(1).upper()
            self.sign = 1 if direction in ("N", "E") else -1
            self.degrees = int(match.group(2)) if match.group(2) else 0
            self.minutes = int(match.group(3)) if match.group(3) else 0
            self.seconds = float(match.group(4)) if match.group(4) else 0.0
            return

        # DMSDegrees ("48°01.3358")
        match = DMS_DEGREES.search(sz_angle)
        if match:
            self.sign = -1 if sz_angle.strip().startswith("-") else 1
            self.degrees = int(match.group(1))
            min_val = float(match.group(2).replace(",", "."))
            self.minutes = int(math.trunc(min_val))
            self.seconds = round((min_val - self.minutes) * 60.0)
            return

    @property
    def value(self) -> float:
        return self.sign * (self.degrees + (self.minutes / 60.0) + (self.seconds / 3600.0))

    @value.setter
    def value(self, val: float) -> None:
        self._init_from_angle(val)

    def to_string(self, dt: DisplayType = DisplayType.DECIMAL) -> str:
        sign_prefix = "-" if self.sign < 0 and dt == DisplayType.DECIMAL else ""
        
        direction_suffix = ""
        if dt == DisplayType.LATITUDE:
            direction_suffix = " N" if self.sign > 0 else " S"
        elif dt == DisplayType.LONGITUDE:
            direction_suffix = " E" if self.sign > 0 else " W"

        return f"{sign_prefix}{self.degrees}° {self.minutes}' {self.seconds:.3f}\"{direction_suffix}"

    def __str__(self) -> str:
        return self.to_string(DisplayType.DECIMAL)
