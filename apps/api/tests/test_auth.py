from __future__ import annotations

import pytest

from myflightbook_api.core.auth import get_current_user
from myflightbook_api.core.config import get_settings


class _FakeResult:
    def scalar_one_or_none(self):
        return None


class _FakeSession:
    def __init__(self) -> None:
        self.statement = None
        self.added = []
        self.committed = False
        self.refreshed = []

    async def execute(self, statement):
        self.statement = statement
        return _FakeResult()

    def add(self, item) -> None:
        self.added.append(item)

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, item) -> None:
        self.refreshed.append(item)


@pytest.mark.asyncio
async def test_get_current_user_uses_default_demo_email_when_called_directly() -> None:
    session = _FakeSession()

    user = await get_current_user(session)

    compiled = session.statement.compile()
    assert get_settings().default_demo_email in compiled.params.values()
    assert session.added[0].email == get_settings().default_demo_email
    assert user.email == get_settings().default_demo_email
    assert session.committed is True
