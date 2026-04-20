from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from myflightbook_api.api.dependencies.auth import VerifiedIdentity
from myflightbook_api.core.auth import IdentityConflictError, IdentityProvisioningError, provision_user_from_identity
from myflightbook_api.core.config import get_settings
from myflightbook_api.db.dependencies import get_db_session
from myflightbook_api.schemas.auth import AuthBootstrapResponse, IdentityLinkRead
from myflightbook_api.schemas.profile import ProfileRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/providers")
async def list_providers() -> dict[str, list[str]]:
    return {"providers": get_settings().enabled_oidc_providers}


@router.post("/bootstrap", response_model=AuthBootstrapResponse, deprecated=True)
@router.post("/login", response_model=AuthBootstrapResponse)
async def login_with_oidc(
    verified_identity: VerifiedIdentity,
    session: AsyncSession = Depends(get_db_session),
) -> AuthBootstrapResponse:
    try:
        user, identity, is_new_user = await provision_user_from_identity(session, verified_identity)
    except IdentityProvisioningError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except IdentityConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return AuthBootstrapResponse(
        user=ProfileRead.model_validate(user),
        identity=IdentityLinkRead.model_validate(identity),
        is_new_user=is_new_user,
    )
