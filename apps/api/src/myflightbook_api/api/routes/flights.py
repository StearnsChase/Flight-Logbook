from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from myflightbook_api.core.auth import get_current_user
from myflightbook_api.db.dependencies import get_db_session
from myflightbook_api.models.aircraft import Aircraft
from myflightbook_api.models.flight import Flight
from myflightbook_api.schemas.flight import FlightCreate, FlightRead, FlightUpdate

router = APIRouter(prefix="/flights", tags=["flights"])


@router.get("", response_model=list[FlightRead])
async def list_flights(session: AsyncSession = Depends(get_db_session)) -> list[FlightRead]:
    user = await get_current_user(session)
    result = await session.execute(
        select(Flight).where(Flight.user_id == user.id).order_by(Flight.flight_date.desc(), Flight.created_at.desc())
    )
    return [FlightRead.model_validate(flight) for flight in result.scalars().all()]


@router.post("", response_model=FlightRead)
async def create_flight(
    payload: FlightCreate,
    session: AsyncSession = Depends(get_db_session)
) -> FlightRead:
    user = await get_current_user(session)
    aircraft_result = await session.execute(
        select(Aircraft).where(Aircraft.id == payload.aircraft_id, Aircraft.owner_user_id == user.id)
    )
    aircraft = aircraft_result.scalar_one_or_none()
    if aircraft is None:
        raise HTTPException(status_code=400, detail="Aircraft must belong to the current user")

    flight = Flight(user_id=user.id, **payload.model_dump())
    session.add(flight)
    await session.commit()
    await session.refresh(flight)
    return FlightRead.model_validate(flight)


@router.get("/{flight_id}", response_model=FlightRead)
async def get_flight(flight_id: str, session: AsyncSession = Depends(get_db_session)) -> FlightRead:
    user = await get_current_user(session)
    result = await session.execute(select(Flight).where(Flight.id == flight_id, Flight.user_id == user.id))
    flight = result.scalar_one_or_none()
    if flight is None:
        raise HTTPException(status_code=404, detail="Flight not found")
    return FlightRead.model_validate(flight)


@router.patch("/{flight_id}", response_model=FlightRead)
async def update_flight(
    flight_id: str,
    payload: FlightUpdate,
    session: AsyncSession = Depends(get_db_session)
) -> FlightRead:
    user = await get_current_user(session)
    result = await session.execute(select(Flight).where(Flight.id == flight_id, Flight.user_id == user.id))
    flight = result.scalar_one_or_none()
    if flight is None:
        raise HTTPException(status_code=404, detail="Flight not found")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(flight, field, value)

    await session.commit()
    await session.refresh(flight)
    return FlightRead.model_validate(flight)
