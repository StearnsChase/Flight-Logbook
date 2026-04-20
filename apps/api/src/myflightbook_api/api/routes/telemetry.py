from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from myflightbook_api.api.dependencies.auth import CurrentUser
from myflightbook_api.db.dependencies import get_db_session
from myflightbook_api.models.media import TelemetryUpload
from myflightbook_api.schemas.telemetry import TelemetryUploadCreate, TelemetryUploadRead

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.get("/uploads", response_model=list[TelemetryUploadRead])
async def list_uploads(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> list[TelemetryUploadRead]:
    result = await session.execute(
        select(TelemetryUpload)
        .where(TelemetryUpload.user_id == current_user.id)
        .order_by(TelemetryUpload.created_at.desc())
    )
    return [TelemetryUploadRead.model_validate(upload) for upload in result.scalars().all()]


@router.post("/uploads", response_model=TelemetryUploadRead)
async def create_upload(
    payload: TelemetryUploadCreate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> TelemetryUploadRead:
    payload_data = payload.model_dump()
    upload = TelemetryUpload(user_id=current_user.id, metadata_json=payload_data.pop("metadata"), **payload_data)
    session.add(upload)
    await session.commit()
    await session.refresh(upload)
    return TelemetryUploadRead.model_validate(upload)
