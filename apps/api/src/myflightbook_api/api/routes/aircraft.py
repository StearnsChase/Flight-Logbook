from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from myflightbook_api.api.dependencies.auth import CurrentUser
from myflightbook_api.db.dependencies import get_db_session
from myflightbook_api.models.aircraft import Aircraft
from myflightbook_api.schemas.aircraft import AircraftCreate, AircraftRead, AircraftUpdate
from myflightbook_api.services.aircraft import (
    UserAircraftConflictError,
    UserAircraftService,
    UserAircraftValidationError,
)

router = APIRouter(prefix="/aircraft", tags=["aircraft"])


@router.get("", response_model=list[AircraftRead])
async def list_aircraft(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> list[AircraftRead]:
    result = await session.execute(
        select(Aircraft).where(Aircraft.owner_user_id == current_user.id).order_by(Aircraft.tail_number)
    )
    return [AircraftRead.model_validate(aircraft) for aircraft in result.scalars().all()]


@router.post("", response_model=AircraftRead)
async def create_aircraft(
    payload: AircraftCreate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> AircraftRead:
    service = UserAircraftService(session)

    try:
        aircraft = await service.create_user_aircraft(owner_user_id=current_user.id, **payload.model_dump())
    except UserAircraftConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except UserAircraftValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await session.commit()
    await session.refresh(aircraft)
    return AircraftRead.model_validate(aircraft)


@router.get("/{aircraft_id}", response_model=AircraftRead)
async def get_aircraft(
    aircraft_id: str,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> AircraftRead:
    result = await session.execute(
        select(Aircraft).where(Aircraft.id == aircraft_id, Aircraft.owner_user_id == current_user.id)
    )
    aircraft = result.scalar_one_or_none()
    if aircraft is None:
        raise HTTPException(status_code=404, detail="Aircraft not found")
    return AircraftRead.model_validate(aircraft)


@router.patch("/{aircraft_id}", response_model=AircraftRead)
async def update_aircraft(
    aircraft_id: str,
    payload: AircraftUpdate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> AircraftRead:
    result = await session.execute(
        select(Aircraft).where(Aircraft.id == aircraft_id, Aircraft.owner_user_id == current_user.id)
    )
    aircraft = result.scalar_one_or_none()
    if aircraft is None:
        raise HTTPException(status_code=404, detail="Aircraft not found")

    service = UserAircraftService(session)

    try:
        await service.update_user_aircraft(aircraft, **payload.model_dump(exclude_none=True))
    except UserAircraftConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except UserAircraftValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await session.commit()
    await session.refresh(aircraft)
    return AircraftRead.model_validate(aircraft)
