from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from myflightbook_api.api.dependencies.auth import CurrentUser
from myflightbook_api.db.dependencies import get_db_session
from myflightbook_api.models.media import ImageAsset
from myflightbook_api.schemas.image import ImageAssetCreate, ImageAssetRead

router = APIRouter(prefix="/images", tags=["images"])


@router.get("", response_model=list[ImageAssetRead])
async def list_images(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> list[ImageAssetRead]:
    result = await session.execute(
        select(ImageAsset).where(ImageAsset.user_id == current_user.id).order_by(ImageAsset.created_at.desc())
    )
    return [ImageAssetRead.model_validate(image) for image in result.scalars().all()]


@router.post("", response_model=ImageAssetRead)
async def create_image(
    payload: ImageAssetCreate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> ImageAssetRead:
    payload_data = payload.model_dump()
    image = ImageAsset(user_id=current_user.id, metadata_json=payload_data.pop("metadata"), **payload_data)
    session.add(image)
    await session.commit()
    await session.refresh(image)
    return ImageAssetRead.model_validate(image)
