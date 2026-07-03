from __future__ import annotations

import asyncio
import httpx
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from myflightbook_api.core.config import get_settings
from myflightbook_api.db.dependencies import get_db_session

router = APIRouter(tags=["Health"])


async def _check_database(db: AsyncSession) -> None:
    await db.execute(text("SELECT 1"))


async def _check_redis_with_socket(redis_url: str, timeout_seconds: float) -> None:
    parsed = urlparse(redis_url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 6379
    use_ssl = parsed.scheme == "rediss"

    async with asyncio.timeout(timeout_seconds):
        reader, writer = await asyncio.open_connection(host=host, port=port, ssl=use_ssl)
        try:
            writer.write(b"*1\r\n$4\r\nPING\r\n")
            await writer.drain()
            reply = await reader.readline()
        finally:
            writer.close()
            await writer.wait_closed()

    if reply.strip().upper() != b"+PONG":
        raise RuntimeError("Redis did not return PONG")


async def _check_redis(redis_url: str, timeout_seconds: float) -> None:
    try:
        from redis import asyncio as redis_asyncio
    except ImportError:
        await _check_redis_with_socket(redis_url, timeout_seconds)
        return

    client = redis_asyncio.from_url(
        redis_url,
        socket_connect_timeout=timeout_seconds,
        socket_timeout=timeout_seconds,
        decode_responses=True,
    )
    try:
        async with asyncio.timeout(timeout_seconds):
            is_healthy = await client.ping()
    finally:
        await client.aclose()

    if not is_healthy:
        raise RuntimeError("Redis ping failed")


async def _check_s3(endpoint_url: str, timeout_seconds: float) -> None:
    timeout = httpx.Timeout(timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        response = await client.get(endpoint_url)
    if response.status_code >= 500:
        raise RuntimeError(f"S3 endpoint returned {response.status_code}")


async def _run_health_checks(db: AsyncSession) -> dict[str, str]:
    settings = get_settings()
    timeout_seconds = settings.healthcheck_timeout_seconds
    results: dict[str, str] = {}
    failures: dict[str, str] = {}

    checks = (
        ("db", _check_database(db)),
        ("redis", _check_redis(settings.redis_url, timeout_seconds)),
        ("s3", _check_s3(settings.s3_endpoint, timeout_seconds)),
    )

    for service_name, probe in checks:
        try:
            await probe
        except Exception as exc:
            failures[service_name] = str(exc)
        else:
            results[service_name] = "ok"

    if failures:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "services": {**results, **{name: "error" for name in failures}},
                "errors": failures,
            },
        )

    return results


@router.get("/health", summary="Perform a Liveness and Readiness check.")
async def health_check(db: AsyncSession = Depends(get_db_session)) -> dict[str, str]:
    return await _run_health_checks(db)


@router.get("/healthz", include_in_schema=False)
async def healthz_check(db: AsyncSession = Depends(get_db_session)) -> dict[str, str]:
    return await _run_health_checks(db)
