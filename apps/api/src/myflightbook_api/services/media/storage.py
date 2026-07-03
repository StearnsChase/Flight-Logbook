from __future__ import annotations

import inspect
import os

from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from myflightbook_api.core.config import Settings, get_settings


def _first_non_empty(*values: str | None) -> str | None:
    for value in values:
        if value is None:
            continue
        stripped = value.strip()
        if stripped:
            return stripped
    return None


def _session_factory() -> Any:
    try:
        import aioboto3
    except ImportError as exc:
        raise RuntimeError("aioboto3 is required for S3-compatible media storage") from exc

    return aioboto3.Session


def _botocore_config(endpoint_url: str | None) -> Any:
    try:
        from botocore.config import Config
    except ImportError as exc:
        raise RuntimeError("botocore is required for S3-compatible media storage") from exc

    addressing_style = "path" if endpoint_url else "auto"
    return Config(signature_version="s3v4", s3={"addressing_style": addressing_style})


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


@dataclass(slots=True, frozen=True)
class S3StorageConfig:
    bucket_name: str
    endpoint_url: str | None
    access_key_id: str | None
    secret_access_key: str | None
    session_token: str | None
    region_name: str
    presigned_upload_ttl_seconds: int = 900

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> S3StorageConfig:
        resolved_settings = settings or get_settings()

        explicit_mfb_endpoint = os.getenv("MFB_S3_ENDPOINT")
        explicit_mfb_bucket = os.getenv("MFB_S3_BUCKET")
        explicit_mfb_access_key = os.getenv("MFB_S3_ACCESS_KEY")
        explicit_mfb_secret_key = os.getenv("MFB_S3_SECRET_KEY")

        endpoint_url = _first_non_empty(
            os.getenv("AWS_ENDPOINT_URL"),
            explicit_mfb_endpoint,
        )
        bucket_name = _first_non_empty(
            os.getenv("AWS_BUCKET_NAME"),
            os.getenv("S3_BUCKET"),
            explicit_mfb_bucket,
            resolved_settings.s3_bucket,
        )
        access_key_id = _first_non_empty(
            os.getenv("AWS_ACCESS_KEY_ID"),
            explicit_mfb_access_key,
            resolved_settings.s3_access_key,
        )
        secret_access_key = _first_non_empty(
            os.getenv("AWS_SECRET_ACCESS_KEY"),
            explicit_mfb_secret_key,
            resolved_settings.s3_secret_key,
        )
        session_token = _first_non_empty(os.getenv("AWS_SESSION_TOKEN"))
        region_name = _first_non_empty(
            os.getenv("AWS_REGION"),
            os.getenv("AWS_DEFAULT_REGION"),
            "us-east-1",
        ) or "us-east-1"
        ttl_value = _first_non_empty(os.getenv("MFB_S3_PRESIGNED_UPLOAD_TTL_SECONDS"), "900")

        if bucket_name is None:
            raise RuntimeError("S3 bucket configuration is missing")

        return cls(
            bucket_name=bucket_name,
            endpoint_url=endpoint_url,
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            session_token=session_token,
            region_name=region_name,
            presigned_upload_ttl_seconds=int(ttl_value),
        )


class S3StorageService:
    def __init__(
        self,
        config: S3StorageConfig | None = None,
        *,
        session_factory: Any | None = None,
        client_config_factory: Any | None = None,
    ) -> None:
        self.config = config or S3StorageConfig.from_settings()
        self._session_factory = session_factory or _session_factory()
        self._client_config_factory = client_config_factory or _botocore_config

    @asynccontextmanager
    async def client(self):
        session = self._session_factory()
        client_kwargs = {
            "aws_access_key_id": self.config.access_key_id,
            "aws_secret_access_key": self.config.secret_access_key,
            "aws_session_token": self.config.session_token,
            "endpoint_url": self.config.endpoint_url,
            "region_name": self.config.region_name,
            "config": self._client_config_factory(self.config.endpoint_url),
        }
        filtered_kwargs = {key: value for key, value in client_kwargs.items() if value is not None}

        async with session.client("s3", **filtered_kwargs) as client:
            yield client

    async def generate_presigned_upload_url(self, object_key: str, content_type: str) -> str:
        normalized_key = self._normalize_object_key(object_key)
        normalized_content_type = self._normalize_content_type(content_type)

        async with self.client() as client:
            presigned_url = await _maybe_await(
                client.generate_presigned_url(
                    ClientMethod="put_object",
                    Params={
                        "Bucket": self.config.bucket_name,
                        "Key": normalized_key,
                        "ContentType": normalized_content_type,
                    },
                    ExpiresIn=self.config.presigned_upload_ttl_seconds,
                    HttpMethod="PUT",
                )
            )

        if not isinstance(presigned_url, str) or not presigned_url:
            raise RuntimeError("S3 client did not return a presigned upload URL")

        return presigned_url

    async def upload_bytes(self, object_key: str, data: bytes, content_type: str) -> None:
        normalized_key = self._normalize_object_key(object_key)
        normalized_content_type = self._normalize_content_type(content_type)
        payload = self._normalize_payload(data)

        async with self.client() as client:
            await _maybe_await(
                client.put_object(
                    Bucket=self.config.bucket_name,
                    Key=normalized_key,
                    Body=payload,
                    ContentType=normalized_content_type,
                )
            )

    async def delete_object(self, object_key: str) -> None:
        normalized_key = self._normalize_object_key(object_key)

        async with self.client() as client:
            await _maybe_await(
                client.delete_object(
                    Bucket=self.config.bucket_name,
                    Key=normalized_key,
                )
            )

    def _normalize_object_key(self, object_key: str) -> str:
        normalized_key = object_key.strip().lstrip("/")
        if not normalized_key:
            raise ValueError("object_key is required")
        return normalized_key

    def _normalize_content_type(self, content_type: str) -> str:
        normalized_content_type = content_type.strip()
        if not normalized_content_type:
            raise ValueError("content_type is required")
        return normalized_content_type

    def _normalize_payload(self, data: bytes | bytearray | memoryview) -> bytes:
        if isinstance(data, memoryview):
            normalized_payload = data.tobytes()
        elif isinstance(data, bytearray):
            normalized_payload = bytes(data)
        elif isinstance(data, bytes):
            normalized_payload = data
        else:
            raise TypeError("data must be bytes-like")

        if not normalized_payload:
            raise ValueError("data is required")

        return normalized_payload


@lru_cache
def get_storage_service() -> S3StorageService:
    return S3StorageService()


async def generate_presigned_upload_url(object_key: str, content_type: str) -> str:
    return await get_storage_service().generate_presigned_upload_url(object_key, content_type)


async def upload_bytes(object_key: str, data: bytes, content_type: str) -> None:
    await get_storage_service().upload_bytes(object_key, data, content_type)


async def delete_object(object_key: str) -> None:
    await get_storage_service().delete_object(object_key)
