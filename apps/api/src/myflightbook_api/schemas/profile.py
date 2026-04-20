from __future__ import annotations

from uuid import UUID

from myflightbook_api.schemas.common import ORMModel


class ProfileRead(ORMModel):
    id: UUID
    email: str
    display_name: str
    given_name: str | None = None
    family_name: str | None = None
    home_airport_code: str | None = None
    locale: str
    legacy_username: str | None = None


class ProfileUpdate(ORMModel):
    display_name: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    home_airport_code: str | None = None
    locale: str | None = None
