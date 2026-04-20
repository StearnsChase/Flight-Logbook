from __future__ import annotations

import json

from functools import lru_cache

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_string_list(value: object) -> list[str]:
    if value is None:
        return []

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        if stripped.startswith("["):
            parsed = json.loads(stripped)
            if not isinstance(parsed, list):
                raise ValueError("Expected a JSON array")
            return [str(item).strip() for item in parsed if str(item).strip()]
        return [item.strip() for item in stripped.split(",") if item.strip()]

    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]

    raise TypeError("Expected a comma-separated string or list of strings")


class OIDCProviderSettings(BaseModel):
    issuer: str
    discovery_url: str | None = None
    jwks_uri: str | None = None
    client_ids: tuple[str, ...] = ()
    algorithms: tuple[str, ...] = ("RS256",)
    issuer_aliases: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_provider(self) -> OIDCProviderSettings:
        if not self.discovery_url and not self.jwks_uri:
            raise ValueError("OIDC providers must define a discovery_url or jwks_uri")
        if not self.algorithms:
            raise ValueError("OIDC providers must allow at least one signing algorithm")
        return self

    @property
    def issuers(self) -> tuple[str, ...]:
        return (self.issuer, *self.issuer_aliases)


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
    oidc_google_client_ids: list[str] = Field(default_factory=list)
    oidc_apple_client_ids: list[str] = Field(default_factory=list)
    oidc_http_timeout_seconds: float = 5.0
    oidc_metadata_cache_ttl_seconds: int = 3600
    oidc_clock_skew_seconds: int = 60
    legacy_mysql_host: str | None = None
    legacy_mysql_port: int = 3306
    legacy_mysql_database: str | None = None
    legacy_mysql_username: str | None = None
    legacy_mysql_password: str | None = None

    @field_validator("oidc_google_client_ids", "oidc_apple_client_ids", mode="before")
    @classmethod
    def parse_oidc_client_ids(cls, value: object) -> list[str]:
        return _parse_string_list(value)

    @property
    def oidc_provider_settings(self) -> dict[str, OIDCProviderSettings]:
        return {
            "google": OIDCProviderSettings(
                issuer="https://accounts.google.com",
                discovery_url="https://accounts.google.com/.well-known/openid-configuration",
                client_ids=tuple(self.oidc_google_client_ids),
                algorithms=("RS256",),
                issuer_aliases=("accounts.google.com",)
            ),
            "apple": OIDCProviderSettings(
                issuer="https://appleid.apple.com",
                discovery_url="https://appleid.apple.com/.well-known/openid-configuration",
                client_ids=tuple(self.oidc_apple_client_ids),
                algorithms=("RS256",)
            ),
        }

    @property
    def enabled_oidc_providers(self) -> list[str]:
        return [
            provider_name for provider_name, provider in self.oidc_provider_settings.items() if provider.client_ids
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
