from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from myflightbook_api.core.auth import IdentityNotLinkedError, get_linked_user_for_identity
from myflightbook_api.core.config import get_settings
from myflightbook_api.core.oidc import (
    OIDCConfigurationError,
    OIDCVerificationError,
    OIDCVerifier,
    VerifiedOIDCIdentity,
)
from myflightbook_api.db.dependencies import get_db_session
from myflightbook_api.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def _bearer_headers(error: str | None = None) -> dict[str, str]:
    challenge = "Bearer"
    if error:
        challenge = f'Bearer error="{error}"'
    return {"WWW-Authenticate": challenge}


async def get_bearer_token(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers=_bearer_headers(),
        )
    return credentials.credentials


@lru_cache
def get_oidc_verifier() -> OIDCVerifier:
    return OIDCVerifier(get_settings())


async def get_verified_oidc_identity(
    token: str = Depends(get_bearer_token),
    verifier: OIDCVerifier = Depends(get_oidc_verifier),
) -> VerifiedOIDCIdentity:
    try:
        return await verifier.verify_token(token)
    except OIDCConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except OIDCVerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers=_bearer_headers("invalid_token"),
        ) from exc


async def get_current_user(
    verified_identity: VerifiedOIDCIdentity = Depends(get_verified_oidc_identity),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    try:
        return await get_linked_user_for_identity(session, verified_identity)
    except IdentityNotLinkedError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers=_bearer_headers("invalid_token"),
        ) from exc


CurrentUser = Annotated[User, Depends(get_current_user)]
VerifiedIdentity = Annotated[VerifiedOIDCIdentity, Depends(get_verified_oidc_identity)]
