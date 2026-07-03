from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
import io
import uuid
from typing import Any, Sequence

from fastapi import UploadFile
from PIL import ExifTags, Image, ImageDraw, ImageFont, ImageOps
from sqlalchemy import select

from myflightbook_api.db.session import SessionLocal
from myflightbook_api.models.media import ImageAsset
from myflightbook_api.models.media import MediaType
from myflightbook_api.models.user import User
from myflightbook_api.services.media.storage import get_storage_service

class ImageStatus(enum.IntEnum):
    PENDING = 0
    UPLOADED = 1
    FAILED = 2
    DELETED = 3

@dataclass
class ProcessingResult:
    status: ImageStatus
    asset_id: uuid.UUID | None
    thumbnail_key: str | None
    web_key: str | None
    error_message: str | None

class ImageProcessingService:
    """
    Handles resizing, watermarking, and metadata extraction for uploaded images.
    """

    @staticmethod
    async def process_and_upload_image(file: UploadFile, user: User) -> ProcessingResult:
        asset_id = uuid.uuid4()
        thumbnail_key: str | None = None
        web_key: str | None = None

        try:
            raw_bytes = await file.read()
            if not raw_bytes:
                raise ValueError("Uploaded file is empty")

            with Image.open(io.BytesIO(raw_bytes)) as original_image:
                metadata = ImageProcessingService._extract_metadata(original_image)
                working_image = ImageOps.exif_transpose(original_image)
                if working_image.mode not in ("RGB", "RGBA"):
                    working_image = working_image.convert("RGB")

                thumbnail_bytes, thumbnail_size = ImageProcessingService._render_variant(working_image, 200)
                web_bytes, web_size = ImageProcessingService._render_variant(working_image, 1024)

            metadata["thumbnail_size"] = {"width": thumbnail_size[0], "height": thumbnail_size[1]}
            metadata["web_size"] = {"width": web_size[0], "height": web_size[1]}

            thumbnail_key = f"images/{user.id}/{asset_id}/thumb.jpg"
            web_key = f"images/{user.id}/{asset_id}/web.jpg"
            storage = get_storage_service()
            await storage.upload_bytes(thumbnail_key, thumbnail_bytes, "image/jpeg")
            await storage.upload_bytes(web_key, web_bytes, "image/jpeg")

            image_asset = ImageAsset(
                id=asset_id,
                user_id=user.id,
                storage_key=web_key,
                original_filename=file.filename or f"{asset_id}.jpg",
                media_type=MediaType.IMAGE,
                metadata_json={
                    **metadata,
                    "thumbnail_key": thumbnail_key,
                    "web_key": web_key,
                },
            )

            async with SessionLocal() as session:
                session.add(image_asset)
                await session.commit()

            return ProcessingResult(
                status=ImageStatus.UPLOADED,
                asset_id=asset_id,
                thumbnail_key=thumbnail_key,
                web_key=web_key,
                error_message=None,
            )
        except Exception as exc:
            return ProcessingResult(
                status=ImageStatus.FAILED,
                asset_id=None,
                thumbnail_key=thumbnail_key,
                web_key=web_key,
                error_message=str(exc),
            )

    @staticmethod
    def generate_watermark(image_bytes: bytes, watermark_text: str) -> bytes:
        with Image.open(io.BytesIO(image_bytes)) as source_image:
            original_format = source_image.format or "JPEG"
            base_image = source_image.convert("RGBA")
            overlay = Image.new("RGBA", base_image.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)
            font = ImageProcessingService._watermark_font(max(base_image.width, base_image.height))
            text = watermark_text.strip() or "MyFlightbook"
            text_box = draw.textbbox((0, 0), text, font=font)
            text_width = text_box[2] - text_box[0]
            text_height = text_box[3] - text_box[1]
            x_pos = max(12, base_image.width - text_width - 18)
            y_pos = max(12, base_image.height - text_height - 18)
            draw.text((x_pos, y_pos), text, font=font, fill=(255, 255, 255, 160))

            watermarked = Image.alpha_composite(base_image, overlay)
            output = io.BytesIO()
            save_format = "PNG" if original_format.upper() == "PNG" else "JPEG"
            if save_format == "JPEG":
                watermarked = watermarked.convert("RGB")
            watermarked.save(output, format=save_format)
            return output.getvalue()

    @staticmethod
    async def delete_image(asset: ImageAsset) -> bool:
        storage = get_storage_service()
        metadata = asset.metadata_json or {}
        keys_to_delete = [asset.storage_key]
        thumbnail_key = metadata.get("thumbnail_key")
        if isinstance(thumbnail_key, str) and thumbnail_key:
            keys_to_delete.append(thumbnail_key)

        try:
            for key in dict.fromkeys(keys_to_delete):
                await storage.delete_object(key)

            async with SessionLocal() as session:
                existing = await session.execute(select(ImageAsset).where(ImageAsset.id == asset.id))
                image_asset = existing.scalar_one_or_none()
                if image_asset is not None:
                    await session.delete(image_asset)
                    await session.commit()

            return True
        except Exception:
            return False

    @staticmethod
    def _render_variant(image: Image.Image, max_size: int) -> tuple[bytes, tuple[int, int]]:
        variant = image.copy()
        variant.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        if variant.mode != "RGB":
            variant = variant.convert("RGB")

        output = io.BytesIO()
        variant.save(output, format="JPEG", quality=88, optimize=True)
        return output.getvalue(), variant.size

    @staticmethod
    def _extract_metadata(image: Image.Image) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "width": image.width,
            "height": image.height,
            "format": image.format,
        }

        exif = image.getexif()
        if not exif:
            return metadata

        date_taken = exif.get(36867) or exif.get(306)
        if date_taken:
            metadata["date_taken"] = str(date_taken)

        try:
            gps_info = exif.get_ifd(34853)
        except Exception:
            gps_info = {}

        latitude = ImageProcessingService._gps_coordinate(
            gps_info.get(2),
            gps_info.get(1),
        )
        longitude = ImageProcessingService._gps_coordinate(
            gps_info.get(4),
            gps_info.get(3),
        )
        if latitude is not None and longitude is not None:
            metadata["gps"] = {"latitude": latitude, "longitude": longitude}

        camera_make = exif.get(271)
        camera_model = exif.get(272)
        if camera_make:
            metadata["camera_make"] = str(camera_make)
        if camera_model:
            metadata["camera_model"] = str(camera_model)

        return metadata

    @staticmethod
    def _gps_coordinate(value: Any, ref: Any) -> float | None:
        if not value or not ref:
            return None

        components = list(value)
        if len(components) != 3:
            return None

        degrees = ImageProcessingService._rational_to_float(components[0])
        minutes = ImageProcessingService._rational_to_float(components[1])
        seconds = ImageProcessingService._rational_to_float(components[2])
        coordinate = degrees + (minutes / 60.0) + (seconds / 3600.0)
        if str(ref).upper() in {"S", "W"}:
            coordinate *= -1
        return coordinate

    @staticmethod
    def _rational_to_float(value: Any) -> float:
        if isinstance(value, tuple):
            numerator, denominator = value
            return float(numerator) / float(denominator or 1)

        numerator = getattr(value, "numerator", None)
        denominator = getattr(value, "denominator", None)
        if numerator is not None and denominator is not None:
            return float(numerator) / float(denominator or 1)

        return float(value)

    @staticmethod
    def _watermark_font(reference_size: int) -> ImageFont.ImageFont:
        font_size = max(12, reference_size // 24)
        for font_name in ("arial.ttf", "DejaVuSans.ttf"):
            try:
                return ImageFont.truetype(font_name, font_size)
            except OSError:
                continue
        return ImageFont.load_default()
