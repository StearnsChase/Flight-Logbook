from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from myflightbook_api.core.auth import get_current_user
from myflightbook_api.db.dependencies import get_db_session
from myflightbook_api.models.user import User
from myflightbook_api.schemas.profile import ProfileRead, ProfileUpdate

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileRead)
async def read_profile(
    session: AsyncSession = Depends(get_db_session)
) -> ProfileRead:
    user = await get_current_user(session)
    return ProfileRead.model_validate(user)


@router.patch("", response_model=ProfileRead)
async def update_profile(
    payload: ProfileUpdate,
    session: AsyncSession = Depends(get_db_session)
) -> ProfileRead:
    user: User = await get_current_user(session)

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(user, field, value)

    await session.commit()
    await session.refresh(user)
    return ProfileRead.model_validate(user)
