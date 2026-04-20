from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from myflightbook_api.db.base import Base
from myflightbook_api.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Flight(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "flights"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    aircraft_id: Mapped[str] = mapped_column(ForeignKey("aircraft.id", ondelete="RESTRICT"), index=True)
    telemetry_upload_id: Mapped[str | None] = mapped_column(ForeignKey("telemetry_uploads.id", ondelete="SET NULL"), nullable=True)

    flight_date: Mapped[date] = mapped_column(Date)
    route: Mapped[str] = mapped_column(String(255), default="")
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_time: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    pic_time: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    sic_time: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    dual_given: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    dual_received: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    cross_country: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    night: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    imc: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    simulated_instrument: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    landings: Mapped[int] = mapped_column(Integer, default=0)
    full_stop_landings_day: Mapped[int] = mapped_column(Integer, default=0)
    full_stop_landings_night: Mapped[int] = mapped_column(Integer, default=0)
    approaches: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped["User"] = relationship(back_populates="flights")
    aircraft: Mapped["Aircraft"] = relationship(back_populates="flights")
    telemetry_upload: Mapped["TelemetryUpload | None"] = relationship(back_populates="flights")
    image_assets: Mapped[list["ImageAsset"]] = relationship(back_populates="flight")


from myflightbook_api.models.aircraft import Aircraft  # noqa: E402
from myflightbook_api.models.media import ImageAsset, TelemetryUpload  # noqa: E402
from myflightbook_api.models.user import User  # noqa: E402
