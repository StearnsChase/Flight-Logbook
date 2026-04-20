from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from myflightbook_api.api.dependencies.auth import CurrentUser
from myflightbook_api.db.dependencies import get_db_session
from myflightbook_api.models.flight import Flight
from myflightbook_api.schemas.totals import TotalsSummaryRead
from myflightbook_api.services.totals import summarize_flights

router = APIRouter(prefix="/totals", tags=["totals"])


@router.get("", response_model=TotalsSummaryRead)
async def get_totals(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> TotalsSummaryRead:
    result = await session.execute(select(Flight).where(Flight.user_id == current_user.id))
    return summarize_flights(result.scalars().all())
