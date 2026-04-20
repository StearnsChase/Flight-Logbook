from __future__ import annotations

import asyncio
import time

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import httpx
import jwt
from jwt import InvalidTokenError, PyJWK

from myflightbook_api.core.config import OIDCProviderSettings, Settings
from myflightbook_api.models.user import IdentityProvider


class OIDCError(Exception):
    """Base error for OIDC verification failures."""


class OIDCConfigurationError(OIDCError):
    """Raised when the API is missing provider configuration."""


class OIDCVerificationError(OIDCError):
    """Raised when a bearer token cannot be verified."""


@dataclass(slots=True, frozen=True)
class VerifiedOIDCIdentity:
    provider: IdentityProvider
    issuer: str
    subject: str
    audience: tuple[str, ...]
    email: str | None
    email_verified: bool
    display_name: str | None
    given_name: str | None
    family_name: str | None
    claims: Mapping[str, Any]


@dataclass(slots=True)
class _CachedJSONDocument:
    payload: dict[str, Any]
    expires_at: float


def _coerce_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    if isinstance(value, int):
        return value != 0
    return False


def _normalize_audience(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    return ()


class OIDCVerifier:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._cache: dict[str, _CachedJSONDocument] = {}
        self._cache_lock = asyncio.Lock()
        self._providers = {
            IdentityProvider(provider_name): provider
            for provider_name, provider in settings.oidc_provider_settings.items()
        }

    async def verify_token(self, token: str) -> VerifiedOIDCIdentity:
        try:
            header = jwt.get_unverified_header(token)
            unverified_claims = jwt.decode(
                token,
                options={
                    "verify_signature": False,
                    "verify_exp": False,
                    "verify_iat": False,
                    "verify_nbf": False,
                    "verify_aud": False,
                    "verify_iss": False,
                },
            )
        except InvalidTokenError as exc:
            raise OIDCVerificationError("Malformed bearer token") from exc

        issuer = str(unverified_claims.get("iss", "")).strip()
        if not issuer:
            raise OIDCVerificationError("Bearer token is missing an issuer claim")

        provider_name, provider = self._resolve_provider(issuer)
        if not provider.client_ids:
            raise OIDCConfigurationError(f"OIDC provider '{provider_name.value}' is not configured")

        signing_algorithm = str(header.get("alg", "")).strip()
        if signing_algorithm not in provider.algorithms:
            raise OIDCVerificationError("Bearer token uses an unsupported signing algorithm")

        metadata = await self._get_provider_metadata(provider)
        jwks_uri = provider.jwks_uri or str(metadata.get("jwks_uri", "")).strip()
        if not jwks_uri:
            raise OIDCConfigurationError(f"OIDC provider '{provider_name.value}' does not publish a JWKS URI")

        signing_key = await self._get_signing_key(
            token=token,
            jwks_uri=jwks_uri,
            expected_algorithm=signing_algorithm,
            allowed_algorithms=provider.algorithms,
        )

        try:
            claims = jwt.decode(
                token,
                key=signing_key.key,
                algorithms=list(provider.algorithms),
                audience=list(provider.client_ids),
                issuer=provider.issuers,
                options={"require": ["iss", "sub", "aud", "exp", "iat"]},
                leeway=self._settings.oidc_clock_skew_seconds,
            )
        except InvalidTokenError as exc:
            raise OIDCVerificationError("Invalid or expired OIDC bearer token") from exc

        self._validate_authorized_party(claims, provider.client_ids)

        return VerifiedOIDCIdentity(
            provider=provider_name,
            issuer=str(claims["iss"]),
            subject=str(claims["sub"]),
            audience=_normalize_audience(claims.get("aud")),
            email=str(claims["email"]).strip() if claims.get("email") else None,
            email_verified=_coerce_bool(claims.get("email_verified")),
            display_name=str(claims["name"]).strip() if claims.get("name") else None,
            given_name=str(claims["given_name"]).strip() if claims.get("given_name") else None,
            family_name=str(claims["family_name"]).strip() if claims.get("family_name") else None,
            claims=claims,
        )

    def _resolve_provider(self, issuer: str) -> tuple[IdentityProvider, OIDCProviderSettings]:
        for provider_name, provider in self._providers.items():
            if issuer in provider.issuers:
                return provider_name, provider
        raise OIDCVerificationError("Bearer token issuer is not supported")

    async def _get_provider_metadata(self, provider: OIDCProviderSettings) -> dict[str, Any]:
        if provider.discovery_url is None:
            return {"issuer": provider.issuer, "jwks_uri": provider.jwks_uri}

        metadata = await self._fetch_json(provider.discovery_url)
        metadata_issuer = str(metadata.get("issuer", "")).strip()
        if metadata_issuer != provider.issuer:
            raise OIDCConfigurationError(
                f"OIDC discovery metadata issuer '{metadata_issuer}' does not match '{provider.issuer}'"
            )
        return metadata

    async def _get_signing_key(
        self,
        *,
        token: str,
        jwks_uri: str,
        expected_algorithm: str,
        allowed_algorithms: tuple[str, ...],
    ) -> PyJWK:
        header = jwt.get_unverified_header(token)
        key_id = str(header.get("kid", "")).strip()
        if not key_id:
            raise OIDCVerificationError("Bearer token is missing a key id")

        jwks = await self._fetch_json(jwks_uri)
        keys = jwks.get("keys")
        if not isinstance(keys, list):
            raise OIDCConfigurationError("JWKS endpoint did not return a 'keys' array")

        for key_data in keys:
            if not isinstance(key_data, dict) or key_data.get("kid") != key_id:
                continue

            key_use = key_data.get("use")
            key_algorithm = key_data.get("alg")
            if key_use not in (None, "sig"):
                continue
            if key_algorithm is not None and key_algorithm not in allowed_algorithms:
                continue

            try:
                return PyJWK.from_dict(key_data, algorithm=expected_algorithm)
            except Exception as exc:  # pragma: no cover - PyJWT surface area is broad.
                raise OIDCConfigurationError("OIDC provider returned an invalid signing key") from exc

        raise OIDCVerificationError("OIDC signing key was not found in the provider JWKS")

    async def _fetch_json(self, url: str) -> dict[str, Any]:
        now = time.monotonic()
        cached = self._cache.get(url)
        if cached is not None and cached.expires_at > now:
            return cached.payload

        async with self._cache_lock:
            cached = self._cache.get(url)
            now = time.monotonic()
            if cached is not None and cached.expires_at > now:
                return cached.payload

            try:
                async with httpx.AsyncClient(
                    follow_redirects=True,
                    timeout=self._settings.oidc_http_timeout_seconds,
                ) as client:
                    response = await client.get(url, headers={"Accept": "application/json"})
                    response.raise_for_status()
                    payload = response.json()
            except (httpx.HTTPError, ValueError) as exc:
                raise OIDCConfigurationError(f"Unable to load OIDC metadata from {url}") from exc

            if not isinstance(payload, dict):
                raise OIDCConfigurationError(f"OIDC endpoint {url} did not return a JSON object")

            ttl_seconds = self._get_cache_ttl_seconds(response.headers.get("Cache-Control"))
            self._cache[url] = _CachedJSONDocument(payload=payload, expires_at=now + ttl_seconds)
            return payload

    def _get_cache_ttl_seconds(self, cache_control: str | None) -> int:
        if cache_control:
            for directive in cache_control.split(","):
                directive = directive.strip()
                if directive.startswith("max-age="):
                    _, value = directive.split("=", 1)
                    try:
                        return max(int(value), 0)
                    except ValueError:
                        break
        return self._settings.oidc_metadata_cache_ttl_seconds

    def _validate_authorized_party(self, claims: dict[str, Any], client_ids: tuple[str, ...]) -> None:
        audience = claims.get("aud")
        azp = claims.get("azp")

        if isinstance(audience, list) and len(audience) > 1 and azp not in client_ids:
            raise OIDCVerificationError("OIDC bearer token is missing a valid authorized party claim")

        if azp is not None and str(azp) not in client_ids:
            raise OIDCVerificationError("OIDC bearer token authorized party is not allowed")
