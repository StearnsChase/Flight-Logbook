from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from myflightbook_api.db.dependencies import get_db_session
from myflightbook_api.models.user import Identity, IdentityProvider, User
from myflightbook_api.schemas.auth import AuthBootstrapRequest, AuthBootstrapResponse, IdentityLinkRead
from myflightbook_api.schemas.profile import ProfileRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/providers")
async def list_providers() -> dict[str, list[str]]:
    return {"providers": ["google", "apple"]}


@router.post("/bootstrap", response_model=AuthBootstrapResponse)
async def bootstrap_auth(
    payload: AuthBootstrapRequest,
    session: AsyncSession = Depends(get_db_session)
) -> AuthBootstrapResponse:
    provider = IdentityProvider(payload.provider)
    query = (
        select(Identity)
        .options(selectinload(Identity.user))
        .where(Identity.provider == provider, Identity.provider_subject == payload.provider_subject)
    )
    result = await session.execute(query)
    identity = result.scalar_one_or_none()
    is_new_user = False

    if identity is None:
        user_result = await session.execute(select(User).where(User.email == payload.email))
        user = user_result.scalar_one_or_none()
        if user is None:
            user = User(
                email=payload.email,
                display_name=payload.display_name,
                given_name=payload.given_name,
                family_name=payload.family_name
            )
            session.add(user)
            await session.flush()
            is_new_user = True

        identity = Identity(
            user=user,
            provider=provider,
            provider_subject=payload.provider_subject,
            email_verified=payload.email_verified
        )
        session.add(identity)
    else:
        user = identity.user

    user.display_name = payload.display_name
    user.given_name = payload.given_name
    user.family_name = payload.family_name
    user.email = payload.email

    await session.commit()
    await session.refresh(user)
    await session.refresh(identity)

    return AuthBootstrapResponse(
        user=ProfileRead.model_validate(user),
        identity=IdentityLinkRead.model_validate(identity),
        is_new_user=is_new_user
    )
