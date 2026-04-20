from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from myflightbook_api.core.auth import get_current_user
from myflightbook_api.db.dependencies import get_db_session
from myflightbook_api.models.flight import Flight
from myflightbook_api.schemas.totals import TotalsSummaryRead
from myflightbook_api.services.totals import summarize_flights

router = APIRouter(prefix="/totals", tags=["totals"])


@router.get("", response_model=TotalsSummaryRead)
async def get_totals(session: AsyncSession = Depends(get_db_session)) -> TotalsSummaryRead:
    user = await get_current_user(session)
    result = await session.execute(select(Flight).where(Flight.user_id == user.id))
    return summarize_flights(result.scalars().all())
