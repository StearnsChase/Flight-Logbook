from __future__ import annotations

import pytest

from myflightbook_api.core.config import Settings
from myflightbook_api.services.media.storage import S3StorageConfig, S3StorageService


class _FakeS3Client:
    def __init__(self) -> None:
        self.presign_calls: list[dict[str, object]] = []
        self.delete_calls: list[dict[str, object]] = []

    def generate_presigned_url(self, **kwargs):
        self.presign_calls.append(kwargs)
        return "https://storage.example/upload"

    async def delete_object(self, **kwargs):
        self.delete_calls.append(kwargs)
        return {"DeleteMarker": True}


class _FakeClientContext:
    def __init__(self, client: _FakeS3Client) -> None:
        self.client = client

    async def __aenter__(self) -> _FakeS3Client:
        return self.client

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class _FakeSession:
    def __init__(self) -> None:
        self.created_clients: list[tuple[str, dict[str, object]]] = []
        self.client_instance = _FakeS3Client()

    def client(self, service_name: str, **kwargs):
        self.created_clients.append((service_name, kwargs))
        return _FakeClientContext(self.client_instance)


@pytest.mark.asyncio
async def test_generate_presigned_upload_url_builds_put_url_with_content_type() -> None:
    fake_session = _FakeSession()
    service = S3StorageService(
        config=S3StorageConfig(
            bucket_name="myflightbook",
            endpoint_url="http://127.0.0.1:9000",
            access_key_id="minio",
            secret_access_key="minio-secret",
            session_token=None,
            region_name="us-east-1",
            presigned_upload_ttl_seconds=600,
        ),
        session_factory=lambda: fake_session,
        client_config_factory=lambda endpoint_url: None,
    )

    url = await service.generate_presigned_upload_url("/uploads/image.jpg", "image/jpeg")

    assert url == "https://storage.example/upload"
    assert fake_session.created_clients[0][0] == "s3"
    call = fake_session.client_instance.presign_calls[0]
    assert call["ClientMethod"] == "put_object"
    assert call["HttpMethod"] == "PUT"
    assert call["ExpiresIn"] == 600
    assert call["Params"] == {
        "Bucket": "myflightbook",
        "Key": "uploads/image.jpg",
        "ContentType": "image/jpeg",
    }


@pytest.mark.asyncio
async def test_delete_object_calls_bucket_and_key() -> None:
    fake_session = _FakeSession()
    service = S3StorageService(
        config=S3StorageConfig(
            bucket_name="myflightbook",
            endpoint_url=None,
            access_key_id=None,
            secret_access_key=None,
            session_token=None,
            region_name="us-east-1",
            presigned_upload_ttl_seconds=900,
        ),
        session_factory=lambda: fake_session,
        client_config_factory=lambda endpoint_url: None,
    )

    await service.delete_object("images/demo.jpg")

    assert fake_session.client_instance.delete_calls == [
        {"Bucket": "myflightbook", "Key": "images/demo.jpg"}
    ]


@pytest.mark.asyncio
async def test_generate_presigned_upload_url_validates_inputs() -> None:
    fake_session = _FakeSession()
    service = S3StorageService(
        config=S3StorageConfig(
            bucket_name="myflightbook",
            endpoint_url=None,
            access_key_id=None,
            secret_access_key=None,
            session_token=None,
            region_name="us-east-1",
            presigned_upload_ttl_seconds=900,
        ),
        session_factory=lambda: fake_session,
        client_config_factory=lambda endpoint_url: None,
    )

    with pytest.raises(ValueError, match="object_key is required"):
        await service.generate_presigned_upload_url("  /  ", "image/jpeg")

    with pytest.raises(ValueError, match="content_type is required"):
        await service.generate_presigned_upload_url("uploads/demo.jpg", "  ")


def test_storage_config_prefers_aws_aliases(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(
        s3_endpoint="http://mfb-local:9000",
        s3_bucket="mfb-bucket",
        s3_access_key="mfb-access",
        s3_secret_key="mfb-secret",
    )

    monkeypatch.setenv("AWS_ENDPOINT_URL", "https://s3.example.com")
    monkeypatch.setenv("AWS_BUCKET_NAME", "aws-bucket")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "aws-access")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "aws-secret")
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    monkeypatch.setenv("MFB_S3_PRESIGNED_UPLOAD_TTL_SECONDS", "1200")

    config = S3StorageConfig.from_settings(settings)

    assert config.endpoint_url == "https://s3.example.com"
    assert config.bucket_name == "aws-bucket"
    assert config.access_key_id == "aws-access"
    assert config.secret_access_key == "aws-secret"
    assert config.region_name == "us-west-2"
    assert config.presigned_upload_ttl_seconds == 1200
