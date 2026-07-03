from __future__ import annotations

import io
from uuid import uuid4

import pytest
from fastapi import UploadFile
from PIL import Image

from myflightbook_api.models.media import ImageAsset, MediaType
from myflightbook_api.models.user import User
from myflightbook_api.services.media import images as image_service
from myflightbook_api.services.media.images import ImageProcessingService, ImageStatus


class _FakeStorageService:
    def __init__(self) -> None:
        self.uploads: list[tuple[str, bytes, str]] = []
        self.deleted: list[str] = []

    async def upload_bytes(self, object_key: str, data: bytes, content_type: str) -> None:
        self.uploads.append((object_key, data, content_type))

    async def delete_object(self, object_key: str) -> None:
        self.deleted.append(object_key)


class _FakeScalarResult:
    def __init__(self, value) -> None:
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _FakeSession:
    def __init__(self, existing=None) -> None:
        self.added = []
        self.deleted = []
        self.committed = False
        self.existing = existing

    def add(self, item) -> None:
        self.added.append(item)

    async def commit(self) -> None:
        self.committed = True

    async def execute(self, statement):
        return _FakeScalarResult(self.existing)

    async def delete(self, item) -> None:
        self.deleted.append(item)


class _FakeSessionContext:
    def __init__(self, session: _FakeSession) -> None:
        self.session = session

    async def __aenter__(self) -> _FakeSession:
        return self.session

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


def _user() -> User:
    user = User(email="pilot@example.com", display_name="Pilot Example")
    user.id = uuid4()
    return user


def _upload_file() -> UploadFile:
    image = Image.new("RGB", (1600, 1200), color=(12, 96, 180))
    output = io.BytesIO()
    image.save(output, format="JPEG")
    output.seek(0)
    return UploadFile(filename="flight.jpg", file=output)


@pytest.mark.asyncio
async def test_process_and_upload_image_creates_variants_and_asset_record(monkeypatch: pytest.MonkeyPatch) -> None:
    storage = _FakeStorageService()
    session = _FakeSession()
    monkeypatch.setattr(image_service, "get_storage_service", lambda: storage)
    monkeypatch.setattr(image_service, "SessionLocal", lambda: _FakeSessionContext(session))

    result = await ImageProcessingService.process_and_upload_image(_upload_file(), _user())

    assert result.status == ImageStatus.UPLOADED
    assert result.asset_id is not None
    assert len(storage.uploads) == 2
    assert session.committed is True
    assert session.added[0].metadata_json["thumbnail_key"] == result.thumbnail_key
    assert session.added[0].metadata_json["web_key"] == result.web_key


def test_generate_watermark_returns_non_empty_bytes() -> None:
    image = Image.new("RGB", (400, 240), color=(40, 40, 40))
    output = io.BytesIO()
    image.save(output, format="JPEG")

    watermarked = ImageProcessingService.generate_watermark(output.getvalue(), "Pilot Example")

    assert watermarked
    assert watermarked != output.getvalue()


@pytest.mark.asyncio
async def test_delete_image_removes_s3_objects_and_metadata_record(monkeypatch: pytest.MonkeyPatch) -> None:
    storage = _FakeStorageService()
    existing_asset = ImageAsset(
        id=uuid4(),
        user_id=str(uuid4()),
        storage_key="images/demo/web.jpg",
        original_filename="demo.jpg",
        media_type=MediaType.IMAGE,
        metadata_json={"thumbnail_key": "images/demo/thumb.jpg"},
    )
    session = _FakeSession(existing=existing_asset)
    monkeypatch.setattr(image_service, "get_storage_service", lambda: storage)
    monkeypatch.setattr(image_service, "SessionLocal", lambda: _FakeSessionContext(session))

    deleted = await ImageProcessingService.delete_image(existing_asset)

    assert deleted is True
    assert storage.deleted == ["images/demo/web.jpg", "images/demo/thumb.jpg"]
    assert session.deleted == [existing_asset]
    assert session.committed is True
