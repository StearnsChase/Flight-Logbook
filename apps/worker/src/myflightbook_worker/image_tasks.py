from __future__ import annotations

import asyncio

from collections.abc import MutableMapping
from io import BytesIO
from pathlib import PurePosixPath
from typing import Any

THUMBNAIL_SIZE = (200, 200)
WEB_SIZE = (1024, 1024)
JPEG_CONTENT_TYPE = "image/jpeg"
DERIVATIVE_CACHE_CONTROL = "public, max-age=31536000, immutable"


def derive_thumbnail_object_keys(image_key: str) -> tuple[str, str]:
    normalized_key = image_key.strip().lstrip("/")
    if not normalized_key:
        raise ValueError("image_key is required")

    path = PurePosixPath(normalized_key)
    parent = "" if str(path.parent) == "." else f"{path.parent.as_posix()}/"
    stem = path.stem if path.suffix else path.name

    return (
        f"{parent}{stem}_thumb.jpg",
        f"{parent}{stem}_web.jpg",
    )


def _load_pillow_modules():
    try:
        from PIL import Image, ImageOps
    except ImportError as exc:
        raise RuntimeError("Pillow is required for worker thumbnail generation") from exc

    return Image, ImageOps


def _build_jpeg_variant_sync(image_bytes: bytes, max_size: tuple[int, int]) -> bytes:
    Image, ImageOps = _load_pillow_modules()

    with Image.open(BytesIO(image_bytes)) as image:
        processed = ImageOps.exif_transpose(image)
        processed = processed.convert("RGB")
        processed.thumbnail(max_size, Image.Resampling.LANCZOS)

        output = BytesIO()
        processed.save(output, format="JPEG", quality=85, optimize=True)
        return output.getvalue()


async def build_jpeg_variant(image_bytes: bytes, max_size: tuple[int, int]) -> bytes:
    return await asyncio.to_thread(_build_jpeg_variant_sync, image_bytes, max_size)


def _require_storage_service(ctx: MutableMapping[str, Any]) -> Any:
    storage_service = ctx.get("storage_service")
    if storage_service is None:
        raise RuntimeError("Worker storage service is not initialized.")
    required_methods = ("normalize_object_key", "download_object_bytes", "upload_object_bytes")
    if not all(callable(getattr(storage_service, method_name, None)) for method_name in required_methods):
        raise RuntimeError("Worker storage service is not initialized.")
    return storage_service


async def generate_thumbnails(ctx: MutableMapping[str, Any], image_key: str) -> dict[str, str]:
    storage_service = _require_storage_service(ctx)
    normalized_key = storage_service.normalize_object_key(image_key)
    thumbnail_key, web_key = derive_thumbnail_object_keys(normalized_key)

    original_bytes = await storage_service.download_object_bytes(normalized_key)

    thumbnail_bytes, web_bytes = await asyncio.gather(
        build_jpeg_variant(original_bytes, THUMBNAIL_SIZE),
        build_jpeg_variant(original_bytes, WEB_SIZE),
    )

    await asyncio.gather(
        storage_service.upload_object_bytes(
            thumbnail_key,
            thumbnail_bytes,
            content_type=JPEG_CONTENT_TYPE,
            cache_control=DERIVATIVE_CACHE_CONTROL,
        ),
        storage_service.upload_object_bytes(
            web_key,
            web_bytes,
            content_type=JPEG_CONTENT_TYPE,
            cache_control=DERIVATIVE_CACHE_CONTROL,
        ),
    )

    return {
        "original_key": normalized_key,
        "thumbnail_key": thumbnail_key,
        "web_key": web_key,
    }
