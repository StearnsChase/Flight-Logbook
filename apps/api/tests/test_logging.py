from __future__ import annotations

from types import SimpleNamespace

import pytest

from fastapi import FastAPI, Request
from starlette.responses import Response

from myflightbook_api.core import logging as logging_module


class _FakeAccessLogger:
    def __init__(self) -> None:
        self.info_calls: list[tuple[str, dict[str, object] | None]] = []
        self.exception_calls: list[tuple[str, dict[str, object] | None]] = []

    def info(self, message: str, *, extra: dict[str, object] | None = None) -> None:
        self.info_calls.append((message, extra))

    def exception(self, message: str, *, extra: dict[str, object] | None = None) -> None:
        self.exception_calls.append((message, extra))


def _request_scope(path: str = "/health") -> dict[str, object]:
    return {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 43123),
        "server": ("testserver", 80),
        "state": {},
    }


@pytest.mark.asyncio
async def test_logging_middleware_adds_request_id_and_logs_access(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_logger = _FakeAccessLogger()
    middleware = logging_module.LoggingMiddleware(FastAPI())
    request = Request(_request_scope("/flights"))
    observed_request_id: dict[str, str] = {}

    async def call_next(req: Request) -> Response:
        observed_request_id["value"] = req.state.request_id
        return Response(status_code=204)

    monkeypatch.setattr(logging_module, "access_logger", fake_logger)

    response = await middleware.dispatch(request, call_next)

    assert response.headers["X-Request-ID"] == observed_request_id["value"]
    assert fake_logger.exception_calls == []
    assert fake_logger.info_calls[0][0] == "http_request_completed"
    assert fake_logger.info_calls[0][1]["extra_fields"]["status_code"] == 204


def test_setup_logging_marks_app_state() -> None:
    app = FastAPI()

    logging_module.setup_logging(app)

    assert app.state.logging_configured is True
