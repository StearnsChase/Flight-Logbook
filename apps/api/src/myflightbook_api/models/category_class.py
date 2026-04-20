from __future__ import annotations

import enum


class CatClassID(enum.IntEnum):
    ASEL = 1
    AMEL = 2
    ASES = 3
    AMES = 4
    GLIDER = 5
    # 6 is unused, left gap for backward compatibility
    HELICOPTER = 7
    GYROPLANE = 8
    POWERED_LIFT = 9
    AIRSHIP = 10
    HOT_AIR_BALLOON = 11
    GAS_BALLOON = 12
    POWERED_PARACHUTE_LAND = 13
    POWERED_PARACHUTE_SEA = 14
    WEIGHT_SHIFT_CONTROL_LAND = 15
    WEIGHT_SHIFT_CONTROL_SEA = 16
    UNMANNED_AERIAL_SYSTEM = 17
    POWERED_PARAGLIDER = 18

    @property
    def is_sea_class(self) -> bool:
        return self in (
            CatClassID.AMES,
            CatClassID.ASES,
            CatClassID.POWERED_PARACHUTE_SEA,
            CatClassID.WEIGHT_SHIFT_CONTROL_SEA,
        )

    @property
    def is_airplane(self) -> bool:
        return self in (CatClassID.ASEL, CatClassID.ASES, CatClassID.AMEL, CatClassID.AMES)

    @property
    def is_powered(self) -> bool:
        return self in (
            CatClassID.AMEL,
            CatClassID.AMES,
            CatClassID.ASEL,
            CatClassID.ASES,
            CatClassID.GYROPLANE,
            CatClassID.HELICOPTER,
            CatClassID.POWERED_LIFT,
            CatClassID.POWERED_PARACHUTE_LAND,
            CatClassID.POWERED_PARACHUTE_SEA,
            CatClassID.AIRSHIP,
        )

    @property
    def is_lighter_than_air(self) -> bool:
        return self in (CatClassID.AIRSHIP, CatClassID.GAS_BALLOON, CatClassID.HOT_AIR_BALLOON)

    @property
    def is_heavier_than_air(self) -> bool:
        return not self.is_lighter_than_air

    @property
    def is_balloon(self) -> bool:
        return self in (CatClassID.GAS_BALLOON, CatClassID.HOT_AIR_BALLOON)

    @property
    def has_engine(self) -> bool:
        return self not in (
            CatClassID.GLIDER,
            CatClassID.GAS_BALLOON,
            CatClassID.HOT_AIR_BALLOON,
            CatClassID.AIRSHIP,
        )

    @property
    def is_manned(self) -> bool:
        return self != CatClassID.UNMANNED_AERIAL_SYSTEM

    @property
    def has_icao(self) -> bool:
        if self in (
            CatClassID.ASEL,
            CatClassID.ASES,
            CatClassID.AMEL,
            CatClassID.AMES,
            CatClassID.HELICOPTER,
            CatClassID.GYROPLANE,
            CatClassID.AIRSHIP,
        ):
            return True
        if self in (
            CatClassID.GAS_BALLOON,
            CatClassID.HOT_AIR_BALLOON,
            CatClassID.GLIDER,
            CatClassID.UNMANNED_AERIAL_SYSTEM,
            CatClassID.WEIGHT_SHIFT_CONTROL_LAND,
            CatClassID.WEIGHT_SHIFT_CONTROL_SEA,
        ):
            return False
        return True
