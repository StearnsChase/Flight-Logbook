from __future__ import annotations

from io import BytesIO

import pytest

from myflightbook_worker import image_tasks


class _FakeStorageService:
    def __init__(self) -> None:
        self.download_calls: list[str] = []
        self.upload_calls: list[dict[str, object]] = []

    def normalize_object_key(self, object_key: str) -> str:
        normalized_key = object_key.strip().lstrip("/")
        if not normalized_key:
            raise ValueError("object_key is required")
        return normalized_key

    async def download_object_bytes(self, object_key: str) -> bytes:
        self.download_calls.append(object_key)
        return b"original-image"

    async def upload_object_bytes(
        self,
        object_key: str,
        data: bytes,
        *,
        content_type: str,
        cache_control: str | None = None,
    ) -> None:
        self.upload_calls.append(
            {
                "object_key": object_key,
                "data": data,
                "content_type": content_type,
                "cache_control": cache_control,
            }
        )


def test_derive_thumbnail_object_keys_preserves_parent_path() -> None:
    thumbnail_key, web_key = image_tasks.derive_thumbnail_object_keys("images/uploads/demo.png")

    assert thumbnail_key == "images/uploads/demo_thumb.jpg"
    assert web_key == "images/uploads/demo_web.jpg"


def test_build_jpeg_variant_sync_resizes_and_reencodes_to_jpeg() -> None:
    from PIL import Image

    source = BytesIO()
    Image.new("RGBA", (1600, 1200), color=(10, 20, 30, 255)).save(source, format="PNG")

    output_bytes = image_tasks._build_jpeg_variant_sync(source.getvalue(), (200, 200))

    with Image.open(BytesIO(output_bytes)) as generated:
        assert generated.format == "JPEG"
        assert generated.size[0] <= 200
        assert generated.size[1] <= 200


@pytest.mark.asyncio
async def test_generate_thumbnails_uploads_both_derivatives(monkeypatch: pytest.MonkeyPatch) -> None:
    storage_service = _FakeStorageService()
    ctx = {"storage_service": storage_service}

    async def _fake_build_variant(image_bytes: bytes, max_size: tuple[int, int]) -> bytes:
        assert image_bytes == b"original-image"
        return f"{max_size[0]}x{max_size[1]}".encode("ascii")

    monkeypatch.setattr(image_tasks, "build_jpeg_variant", _fake_build_variant)

    result = await image_tasks.generate_thumbnails(ctx, "/images/demo.png")

    assert result == {
        "original_key": "images/demo.png",
        "thumbnail_key": "images/demo_thumb.jpg",
        "web_key": "images/demo_web.jpg",
    }
    assert storage_service.download_calls == ["images/demo.png"]
    assert storage_service.upload_calls == [
        {
            "object_key": "images/demo_thumb.jpg",
            "data": b"200x200",
            "content_type": "image/jpeg",
            "cache_control": image_tasks.DERIVATIVE_CACHE_CONTROL,
        },
        {
            "object_key": "images/demo_web.jpg",
            "data": b"1024x1024",
            "content_type": "image/jpeg",
            "cache_control": image_tasks.DERIVATIVE_CACHE_CONTROL,
        },
    ]
