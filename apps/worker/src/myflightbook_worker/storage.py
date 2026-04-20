from __future__ import annotations

import inspect
import os

from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any


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
        raise RuntimeError("aioboto3 is required for worker S3-compatible storage access") from exc

    return aioboto3.Session


def _botocore_config(endpoint_url: str | None) -> Any:
    try:
        from botocore.config import Config
    except ImportError as exc:
        raise RuntimeError("botocore is required for worker S3-compatible storage access") from exc

    addressing_style = "path" if endpoint_url else "auto"
    return Config(signature_version="s3v4", s3={"addressing_style": addressing_style})


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


async def _close_streaming_body(body: Any) -> None:
    close_method = getattr(body, "close", None)
    if callable(close_method):
        await _maybe_await(close_method())


@dataclass(slots=True, frozen=True)
class S3StorageConfig:
    bucket_name: str
    endpoint_url: str | None
    access_key_id: str | None
    secret_access_key: str | None
    session_token: str | None
    region_name: str

    @classmethod
    def from_env(cls) -> S3StorageConfig:
        bucket_name = _first_non_empty(
            os.getenv("AWS_BUCKET_NAME"),
            os.getenv("S3_BUCKET"),
            os.getenv("MFB_S3_BUCKET"),
        )
        endpoint_url = _first_non_empty(
            os.getenv("AWS_ENDPOINT_URL"),
            os.getenv("MFB_S3_ENDPOINT"),
        )
        access_key_id = _first_non_empty(
            os.getenv("AWS_ACCESS_KEY_ID"),
            os.getenv("MFB_S3_ACCESS_KEY"),
        )
        secret_access_key = _first_non_empty(
            os.getenv("AWS_SECRET_ACCESS_KEY"),
            os.getenv("MFB_S3_SECRET_KEY"),
        )
        session_token = _first_non_empty(os.getenv("AWS_SESSION_TOKEN"))
        region_name = _first_non_empty(
            os.getenv("AWS_REGION"),
            os.getenv("AWS_DEFAULT_REGION"),
            "us-east-1",
        ) or "us-east-1"

        if bucket_name is None:
            raise RuntimeError("S3 bucket configuration is missing for the worker")

        return cls(
            bucket_name=bucket_name,
            endpoint_url=endpoint_url,
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            session_token=session_token,
            region_name=region_name,
        )


class S3StorageService:
    def __init__(
        self,
        config: S3StorageConfig | None = None,
        *,
        session_factory: Any | None = None,
        client_config_factory: Any | None = None,
    ) -> None:
        self.config = config or S3StorageConfig.from_env()
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

    def normalize_object_key(self, object_key: str) -> str:
        normalized_key = object_key.strip().lstrip("/")
        if not normalized_key:
            raise ValueError("object_key is required")
        return normalized_key

    async def download_object_bytes(self, object_key: str) -> bytes:
        normalized_key = self.normalize_object_key(object_key)

        async with self.client() as client:
            response = await _maybe_await(
                client.get_object(
                    Bucket=self.config.bucket_name,
                    Key=normalized_key,
                )
            )
            body = response["Body"]
            try:
                return await _maybe_await(body.read())
            finally:
                await _close_streaming_body(body)

    async def upload_object_bytes(
        self,
        object_key: str,
        data: bytes,
        *,
        content_type: str,
        cache_control: str | None = None,
    ) -> None:
        normalized_key = self.normalize_object_key(object_key)
        normalized_content_type = content_type.strip()
        if not normalized_content_type:
            raise ValueError("content_type is required")

        payload = {
            "Bucket": self.config.bucket_name,
            "Key": normalized_key,
            "Body": data,
            "ContentType": normalized_content_type,
        }
        if cache_control:
            payload["CacheControl"] = cache_control

        async with self.client() as client:
            await _maybe_await(client.put_object(**payload))
