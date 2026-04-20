from __future__ import annotations

import enum

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from myflightbook_api.db.base import Base
from myflightbook_api.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


def _enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    return [item.value for item in enum_cls]


class IdentityProvider(str, enum.Enum):
    GOOGLE = "google"
    APPLE = "apple"


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    given_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    family_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    locale: Mapped[str] = mapped_column(String(16), default="en-US")
    home_airport_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    legacy_username: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    identities: Mapped[list["Identity"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    aircraft: Mapped[list["Aircraft"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    flights: Mapped[list["Flight"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    telemetry_uploads: Mapped[list["TelemetryUpload"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    image_assets: Mapped[list["ImageAsset"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Identity(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "identities"
    __table_args__ = (UniqueConstraint("provider", "provider_subject", name="uq_identity_provider_subject"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    provider: Mapped[IdentityProvider] = mapped_column(
        Enum(IdentityProvider, name="identity_provider", values_callable=_enum_values)
    )
    provider_subject: Mapped[str] = mapped_column(String(255))
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped[User] = relationship(back_populates="identities")


from myflightbook_api.models.aircraft import Aircraft  # noqa: E402
from myflightbook_api.models.flight import Flight  # noqa: E402
from myflightbook_api.models.media import ImageAsset, TelemetryUpload  # noqa: E402
