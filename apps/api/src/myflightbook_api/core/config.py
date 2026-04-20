from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MFB_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    project_name: str = "MyFlightbook API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+asyncpg://myflightbook:myflightbook@127.0.0.1:5432/myflightbook"
    sql_echo: bool = False
    cors_origins: list[str] = Field(default_factory=lambda: ["http://127.0.0.1:3000", "http://localhost:3000"])
    s3_endpoint: str = "http://127.0.0.1:9000"
    s3_bucket: str = "myflightbook"
    s3_access_key: str = "myflightbook"
    s3_secret_key: str = "myflightbook"
    default_demo_email: str = "demo@myflightbook.local"
    legacy_mysql_host: str | None = None
    legacy_mysql_port: int = 3306
    legacy_mysql_database: str | None = None
    legacy_mysql_username: str | None = None
    legacy_mysql_password: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
