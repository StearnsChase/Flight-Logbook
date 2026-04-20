from __future__ import annotations

import enum

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from myflightbook_api.db.base import Base


class AllowedAircraftTypes(enum.IntEnum):
    ANY = 0
    SIMULATOR_ONLY = 1
    SIM_OR_ANONYMOUS = 2


class TurbineLevel(enum.IntEnum):
    PISTON = 0
    TURBO_PROP = 1
    JET = 2
    UNSPECIFIED_TURBINE = 3
    ELECTRIC = 4


class AvionicsTechnologyType(enum.IntEnum):
    NONE = 0
    GLASS = 1
    TAA = 2


class Manufacturer(Base):
    __tablename__ = "manufacturers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    allowed_types: Mapped[AllowedAircraftTypes] = mapped_column(Enum(AllowedAircraftTypes), default=AllowedAircraftTypes.ANY)

    models: Mapped[list["MakeModel"]] = relationship(back_populates="manufacturer")


class MakeModel(Base):
    __tablename__ = "make_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    manufacturer_id: Mapped[int] = mapped_column(ForeignKey("manufacturers.id", ondelete="CASCADE"), index=True)
    category_class_id: Mapped[int] = mapped_column(Integer, index=True)  # Maps to CatClassID IntEnum
    
    model: Mapped[str] = mapped_column(String(44))
    model_name: Mapped[str] = mapped_column(String(44), default="")
    type_name: Mapped[str] = mapped_column(String(44), default="")
    family_name: Mapped[str] = mapped_column(String(255), default="")
    army_mds: Mapped[str] = mapped_column(String(44), default="")
    
    allowed_types: Mapped[AllowedAircraftTypes] = mapped_column(Enum(AllowedAircraftTypes), default=AllowedAircraftTypes.ANY)
    engine_type: Mapped[TurbineLevel] = mapped_column(Enum(TurbineLevel), default=TurbineLevel.PISTON)
    
    is_complex: Mapped[bool] = mapped_column(Boolean, default=False)
    is_high_perf: Mapped[bool] = mapped_column(Boolean, default=False)
    is_200hp: Mapped[bool] = mapped_column(Boolean, default=False)
    is_tailwheel: Mapped[bool] = mapped_column(Boolean, default=False)
    is_constant_prop: Mapped[bool] = mapped_column(Boolean, default=False)
    has_flaps: Mapped[bool] = mapped_column(Boolean, default=False)
    is_retract: Mapped[bool] = mapped_column(Boolean, default=False)
    is_all_glass: Mapped[bool] = mapped_column(Boolean, default=False)
    is_all_taa: Mapped[bool] = mapped_column(Boolean, default=False)
    is_motor_glider: Mapped[bool] = mapped_column(Boolean, default=False)
    is_multi_helicopter: Mapped[bool] = mapped_column(Boolean, default=False)
    is_certified_single_pilot: Mapped[bool] = mapped_column(Boolean, default=False)

    manufacturer: Mapped["Manufacturer"] = relationship(back_populates="models")

    @property
    def avionics_technology(self) -> AvionicsTechnologyType:
        if self.is_all_taa and self.is_all_glass:
            return AvionicsTechnologyType.TAA
        if self.is_all_glass:
            return AvionicsTechnologyType.GLASS
        return AvionicsTechnologyType.NONE

    @property
    def display_name(self) -> str:
        return f"{self.manufacturer.name} {self.model_display_name}".strip() if self.manufacturer else self.model_display_name

    @property
    def model_display_name(self) -> str:
        parts = []
        if self.type_name:
            parts.append(f"{self.model} (Type: {self.type_name})")
        else:
            parts.append(self.model)
            
        if self.model_name:
            parts.append(f'"{self.model_name}"')
            
        return " ".join(parts).strip()
