from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from myflightbook_api.db.base import Base


class RegenUnit(enum.IntEnum):
    NONE = 0
    DAYS = 1
    CALENDAR_MONTHS = 2
    HOURS = 3


class DeadlineMode(enum.IntEnum):
    CALENDAR = 0
    HOURS = 1


class Deadline(Base):
    __tablename__ = "deadlines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Nullable because it could be a shared aircraft deadline
    username_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    
    name: Mapped[str] = mapped_column(String(255))
    expiration: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    regen_span: Mapped[int] = mapped_column(Integer, default=0)
    regen_type: Mapped[RegenUnit] = mapped_column(Enum(RegenUnit), default=RegenUnit.NONE)
    
    # Optional relation to a specific aircraft (for shared/aircraft-specific deadlines like annual inspections)
    aircraft_id: Mapped[int | None] = mapped_column(ForeignKey("aircraft.id", ondelete="CASCADE"), nullable=True)
    aircraft_hours: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    user: Mapped["User | None"] = relationship()
    aircraft: Mapped["Aircraft | None"] = relationship()

    @property
    def mode(self) -> DeadlineMode:
        return DeadlineMode.HOURS if self.aircraft_id and self.aircraft_hours else DeadlineMode.CALENDAR

    @property
    def uses_hours(self) -> bool:
        return self.mode == DeadlineMode.HOURS

    @property
    def is_shared_aircraft_deadline(self) -> bool:
        return not self.username_id and self.aircraft_id is not None
