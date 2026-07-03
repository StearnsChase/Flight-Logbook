from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from myflightbook_api.db.base import Base
from myflightbook_api.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Aircraft(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "aircraft"

    owner_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    tail_number: Mapped[str] = mapped_column(String(30))
    display_name: Mapped[str] = mapped_column(String(255))
    model_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    category_class: Mapped[str | None] = mapped_column(String(100), nullable=True)
    engine_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_complex: Mapped[bool] = mapped_column(Boolean, default=False)
    is_high_performance: Mapped[bool] = mapped_column(Boolean, default=False)
    is_retractable: Mapped[bool] = mapped_column(Boolean, default=False)
    last_altimeter: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_vor: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_static: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_transponder: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_annual: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_elt: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    registration_due: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    public_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    private_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_flags: Mapped[int] = mapped_column(Integer, default=0)
    revision: Mapped[int] = mapped_column(Integer, default=0)

    owner: Mapped["User"] = relationship(back_populates="aircraft")
    flights: Mapped[list["Flight"]] = relationship(back_populates="aircraft")


from myflightbook_api.models.flight import Flight  # noqa: E402
from myflightbook_api.models.user import User  # noqa: E402
