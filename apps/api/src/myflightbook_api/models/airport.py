from __future__ import annotations

from decimal import Decimal

from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from myflightbook_api.db.base import Base
from myflightbook_api.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Airport(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "airports"
    __table_args__ = (UniqueConstraint("code", "facility_type", name="uq_airports_code_type"),)

    code: Mapped[str] = mapped_column(String(10))
    facility_type: Mapped[str] = mapped_column(String(5), default="A")
    name: Mapped[str] = mapped_column(String(255))
    country: Mapped[str | None] = mapped_column(String(255), nullable=True)
    admin1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6))
    position: Mapped[str | None] = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=True)
    source_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    source_user: Mapped["User | None"] = relationship()


from myflightbook_api.models.user import User  # noqa: E402
