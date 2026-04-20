from __future__ import annotations

from typing import Literal

from myflightbook_api.schemas.common import ORMModel
from myflightbook_api.schemas.profile import ProfileRead


AuthProvider = Literal["google", "apple"]


class IdentityLinkRead(ORMModel):
    provider: AuthProvider
    provider_subject: str
    email_verified: bool


class AuthBootstrapRequest(ORMModel):
    provider: AuthProvider
    provider_subject: str
    email: str
    display_name: str
    given_name: str | None = None
    family_name: str | None = None
    email_verified: bool = True


class AuthBootstrapResponse(ORMModel):
    user: ProfileRead
    identity: IdentityLinkRead
    is_new_user: bool
