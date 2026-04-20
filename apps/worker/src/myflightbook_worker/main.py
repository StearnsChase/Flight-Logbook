from __future__ import annotations

import asyncio

from collections.abc import MutableMapping
from enum import Enum
from functools import lru_cache
from typing import Any
from uuid import UUID

import sqlalchemy as sa

from arq.connections import RedisSettings
from arq.worker import run_worker
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from myflightbook_worker.image_tasks import generate_thumbnails
from myflightbook_worker.storage import S3StorageService


class WorkerAppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MFB_", env_file=".env", case_sensitive=False)

    worker_queue: str = "telemetry"
    database_url: str = "postgresql+asyncpg://myflightbook:myflightbook@127.0.0.1:5432/myflightbook"
    redis_url: str = "redis://127.0.0.1:6379/0"
    worker_max_jobs: int = 4
    job_timeout_seconds: int = 30
    sql_echo: bool = False


@lru_cache
def get_settings() -> WorkerAppSettings:
    return WorkerAppSettings()


class ParseStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    PARSED = "parsed"
    PROCESSED = "processed"
    FAILED = "failed"


parse_status_enum = sa.Enum(
    *(status.value for status in ParseStatus),
    name="parse_status",
    create_type=False,
)

metadata = sa.MetaData()
telemetry_uploads = sa.Table(
    "telemetry_uploads",
    metadata,
    sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
    sa.Column("parse_status", parse_status_enum, nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
)


async def _set_upload_status(
    session_factory: async_sessionmaker[AsyncSession],
    upload_id: UUID,
    status: ParseStatus,
) -> None:
    async with session_factory() as session:
        result = await session.execute(
            sa.update(telemetry_uploads)
            .where(telemetry_uploads.c.id == upload_id)
            .values(parse_status=status.value, updated_at=sa.func.now())
        )

        if result.rowcount == 0:
            await session.rollback()
            raise LookupError(f"Telemetry upload {upload_id} was not found.")

        await session.commit()


async def startup(ctx: MutableMapping[str, Any]) -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=settings.sql_echo)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    ctx["settings"] = settings
    ctx["engine"] = engine
    ctx["session_factory"] = session_factory
    ctx["storage_service"] = S3StorageService()


async def shutdown(ctx: MutableMapping[str, Any]) -> None:
    engine = ctx.get("engine")
    if isinstance(engine, AsyncEngine):
        await engine.dispose()


async def process_telemetry(ctx: MutableMapping[str, Any], upload_id: UUID | str) -> str:
    upload_uuid = upload_id if isinstance(upload_id, UUID) else UUID(str(upload_id))
    session_factory = ctx["session_factory"]

    if not isinstance(session_factory, async_sessionmaker):
        raise RuntimeError("Worker session factory is not initialized.")

    await _set_upload_status(session_factory, upload_uuid, ParseStatus.PROCESSING)

    try:
        await asyncio.sleep(2)
        await _set_upload_status(session_factory, upload_uuid, ParseStatus.PROCESSED)
    except Exception:
        await _set_upload_status(session_factory, upload_uuid, ParseStatus.FAILED)
        raise

    return str(upload_uuid)


class WorkerSettings:
    functions = [process_telemetry, generate_thumbnails]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
    queue_name = get_settings().worker_queue
    max_jobs = get_settings().worker_max_jobs
    job_timeout = get_settings().job_timeout_seconds


def main() -> None:
    run_worker(WorkerSettings)


if __name__ == "__main__":
    main()
