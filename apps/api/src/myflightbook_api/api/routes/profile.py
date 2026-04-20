from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from myflightbook_api.api.dependencies.auth import CurrentUser
from myflightbook_api.db.dependencies import get_db_session
from myflightbook_api.schemas.profile import ProfileRead, ProfileUpdate

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileRead)
async def read_profile(current_user: CurrentUser) -> ProfileRead:
    return ProfileRead.model_validate(current_user)


@router.patch("", response_model=ProfileRead)
async def update_profile(
    payload: ProfileUpdate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> ProfileRead:
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)

    await session.commit()
    await session.refresh(current_user)
    return ProfileRead.model_validate(current_user)
