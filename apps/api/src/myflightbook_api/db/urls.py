from __future__ import annotations

from sqlalchemy.engine import make_url


ASYNC_TO_SYNC_DRIVER_MAP = {
    "postgresql+asyncpg": "postgresql+psycopg",
}


def to_sync_database_url(database_url: str) -> str:
    url = make_url(database_url)
    sync_driver = ASYNC_TO_SYNC_DRIVER_MAP.get(url.drivername, url.drivername)
    return url.set(drivername=sync_driver).render_as_string(hide_password=False)
