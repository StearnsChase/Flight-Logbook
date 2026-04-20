from myflightbook_api.db.urls import to_sync_database_url


def test_to_sync_database_url_converts_asyncpg_driver() -> None:
    source = "postgresql+asyncpg://myflightbook:myflightbook@127.0.0.1:5432/myflightbook"
    expected = "postgresql+psycopg://myflightbook:myflightbook@127.0.0.1:5432/myflightbook"
    assert to_sync_database_url(source) == expected


def test_to_sync_database_url_leaves_sync_driver_unchanged() -> None:
    source = "postgresql+psycopg://myflightbook:myflightbook@127.0.0.1:5432/myflightbook"
    assert to_sync_database_url(source) == source
