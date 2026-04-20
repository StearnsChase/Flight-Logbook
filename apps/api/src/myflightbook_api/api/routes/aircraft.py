from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from myflightbook_api.core.auth import get_current_user
from myflightbook_api.db.dependencies import get_db_session
from myflightbook_api.models.aircraft import Aircraft
from myflightbook_api.schemas.aircraft import AircraftCreate, AircraftRead, AircraftUpdate

router = APIRouter(prefix="/aircraft", tags=["aircraft"])


@router.get("", response_model=list[AircraftRead])
async def list_aircraft(session: AsyncSession = Depends(get_db_session)) -> list[AircraftRead]:
    user = await get_current_user(session)
    result = await session.execute(select(Aircraft).where(Aircraft.owner_user_id == user.id).order_by(Aircraft.tail_number))
    return [AircraftRead.model_validate(aircraft) for aircraft in result.scalars().all()]


@router.post("", response_model=AircraftRead)
async def create_aircraft(
    payload: AircraftCreate,
    session: AsyncSession = Depends(get_db_session)
) -> AircraftRead:
    user = await get_current_user(session)
    aircraft = Aircraft(owner_user_id=user.id, **payload.model_dump())
    session.add(aircraft)
    await session.commit()
    await session.refresh(aircraft)
    return AircraftRead.model_validate(aircraft)


@router.get("/{aircraft_id}", response_model=AircraftRead)
async def get_aircraft(aircraft_id: str, session: AsyncSession = Depends(get_db_session)) -> AircraftRead:
    user = await get_current_user(session)
    result = await session.execute(
        select(Aircraft).where(Aircraft.id == aircraft_id, Aircraft.owner_user_id == user.id)
    )
    aircraft = result.scalar_one_or_none()
    if aircraft is None:
        raise HTTPException(status_code=404, detail="Aircraft not found")
    return AircraftRead.model_validate(aircraft)


@router.patch("/{aircraft_id}", response_model=AircraftRead)
async def update_aircraft(
    aircraft_id: str,
    payload: AircraftUpdate,
    session: AsyncSession = Depends(get_db_session)
) -> AircraftRead:
    user = await get_current_user(session)
    result = await session.execute(
        select(Aircraft).where(Aircraft.id == aircraft_id, Aircraft.owner_user_id == user.id)
    )
    aircraft = result.scalar_one_or_none()
    if aircraft is None:
        raise HTTPException(status_code=404, detail="Aircraft not found")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(aircraft, field, value)

    await session.commit()
    await session.refresh(aircraft)
    return AircraftRead.model_validate(aircraft)
