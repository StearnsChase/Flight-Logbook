from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from myflightbook_api.core.config import get_settings
from myflightbook_api.models.user import User


async def get_current_user(
    session: AsyncSession,
    demo_email: str | None = None
) -> User:
    settings = get_settings()
    email = demo_email or settings.default_demo_email
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(email=email, display_name="Demo Pilot", locale="en-US")
        session.add(user)
        await session.commit()
        await session.refresh(user)

    return user
