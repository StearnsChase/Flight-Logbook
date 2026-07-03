from __future__ import annotations

import pytest

from fastapi import HTTPException

from myflightbook_api.api.routes import health as health_routes


class _FakeSession:
    def __init__(self) -> None:
        self.executed = []

    async def execute(self, statement) -> None:
        self.executed.append(statement)


@pytest.mark.asyncio
async def test_health_check_returns_ok_for_all_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession()

    async def fake_check_redis(redis_url: str, timeout_seconds: float) -> None:
        assert redis_url == health_routes.get_settings().redis_url
        assert timeout_seconds == health_routes.get_settings().healthcheck_timeout_seconds

    async def fake_check_s3(endpoint_url: str, timeout_seconds: float) -> None:
        assert endpoint_url == health_routes.get_settings().s3_endpoint
        assert timeout_seconds == health_routes.get_settings().healthcheck_timeout_seconds

    monkeypatch.setattr(health_routes, "_check_redis", fake_check_redis)
    monkeypatch.setattr(health_routes, "_check_s3", fake_check_s3)

    result = await health_routes.health_check(session)

    assert result == {"db": "ok", "redis": "ok", "s3": "ok"}
    assert len(session.executed) == 1


@pytest.mark.asyncio
async def test_health_check_returns_503_when_a_dependency_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession()

    async def fake_check_redis(redis_url: str, timeout_seconds: float) -> None:
        raise RuntimeError("redis offline")

    async def fake_check_s3(endpoint_url: str, timeout_seconds: float) -> None:
        return None

    monkeypatch.setattr(health_routes, "_check_redis", fake_check_redis)
    monkeypatch.setattr(health_routes, "_check_s3", fake_check_s3)

    with pytest.raises(HTTPException) as exc_info:
        await health_routes.health_check(session)

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail["services"] == {"db": "ok", "redis": "error", "s3": "ok"}
    assert exc_info.value.detail["errors"] == {"redis": "redis offline"}
