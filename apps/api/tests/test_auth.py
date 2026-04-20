from __future__ import annotations

import json
import time

import jwt
import pytest

from cryptography.hazmat.primitives.asymmetric import rsa
from jwt import algorithms

from myflightbook_api.core.auth import (
    IdentityNotLinkedError,
    get_linked_user_for_identity,
    provision_user_from_identity,
)
from myflightbook_api.core.config import Settings
from myflightbook_api.core.oidc import OIDCVerifier, VerifiedOIDCIdentity
from myflightbook_api.models.user import Identity, IdentityProvider, User


class _FakeResult:
    def __init__(self, value) -> None:
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _FakeSession:
    def __init__(self, results: list[object | None]) -> None:
        self._results = iter(results)
        self.statements = []
        self.added = []
        self.committed = False
        self.flushed = False
        self.refreshed = []

    async def execute(self, statement):
        self.statements.append(statement)
        return _FakeResult(next(self._results))

    def add(self, item) -> None:
        self.added.append(item)

    async def flush(self) -> None:
        self.flushed = True

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, item) -> None:
        self.refreshed.append(item)


def _verified_identity(**overrides) -> VerifiedOIDCIdentity:
    base_claims = {
        "iss": "https://accounts.google.com",
        "sub": "google-subject",
        "aud": "google-client-id",
        "email": "pilot@example.com",
        "email_verified": True,
        "name": "Pilot Example",
        "given_name": "Pilot",
        "family_name": "Example",
    }
    base_claims.update(overrides.pop("claims", {}))

    payload = {
        "provider": IdentityProvider.GOOGLE,
        "issuer": "https://accounts.google.com",
        "subject": "google-subject",
        "audience": ("google-client-id",),
        "email": "pilot@example.com",
        "email_verified": True,
        "display_name": "Pilot Example",
        "given_name": "Pilot",
        "family_name": "Example",
        "claims": base_claims,
    }
    payload.update(overrides)
    return VerifiedOIDCIdentity(**payload)


@pytest.mark.asyncio
async def test_oidc_verifier_accepts_a_google_id_token(monkeypatch) -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_jwk = json.loads(algorithms.RSAAlgorithm.to_jwk(private_key.public_key()))
    public_jwk["kid"] = "kid-1"

    verifier = OIDCVerifier(Settings(oidc_google_client_ids=["google-client-id"]))

    async def fake_fetch_json(url: str) -> dict[str, object]:
        if url.endswith("openid-configuration"):
            return {
                "issuer": "https://accounts.google.com",
                "jwks_uri": "https://issuer.example/keys",
            }
        if url.endswith("/keys"):
            return {"keys": [public_jwk]}
        raise AssertionError(url)

    monkeypatch.setattr(verifier, "_fetch_json", fake_fetch_json)

    now = int(time.time())
    token = jwt.encode(
        {
            "iss": "https://accounts.google.com",
            "sub": "google-subject",
            "aud": "google-client-id",
            "exp": now + 300,
            "iat": now,
            "email": "pilot@example.com",
            "email_verified": True,
            "name": "Pilot Example",
            "given_name": "Pilot",
            "family_name": "Example",
        },
        private_key,
        algorithm="RS256",
        headers={"kid": "kid-1"},
    )

    identity = await verifier.verify_token(token)

    assert identity.provider is IdentityProvider.GOOGLE
    assert identity.subject == "google-subject"
    assert identity.email == "pilot@example.com"
    assert identity.email_verified is True


@pytest.mark.asyncio
async def test_get_linked_user_for_identity_requires_a_local_link() -> None:
    session = _FakeSession([None])

    with pytest.raises(IdentityNotLinkedError):
        await get_linked_user_for_identity(session, _verified_identity())


@pytest.mark.asyncio
async def test_provision_user_from_identity_creates_a_new_user_and_link() -> None:
    session = _FakeSession([None, None])

    user, identity, is_new_user = await provision_user_from_identity(session, _verified_identity())

    assert is_new_user is True
    assert user.email == "pilot@example.com"
    assert user.display_name == "Pilot Example"
    assert identity.provider is IdentityProvider.GOOGLE
    assert identity.provider_subject == "google-subject"
    assert session.flushed is True
    assert session.committed is True


@pytest.mark.asyncio
async def test_get_linked_user_for_identity_returns_the_existing_user() -> None:
    user = User(
        email="pilot@example.com",
        display_name="Pilot Example",
        given_name="Pilot",
        family_name="Example",
        locale="en-US",
        is_active=True,
    )
    identity = Identity(
        user=user,
        provider=IdentityProvider.GOOGLE,
        provider_subject="google-subject",
        email_verified=True,
    )
    session = _FakeSession([identity])

    linked_user = await get_linked_user_for_identity(session, _verified_identity())

    assert linked_user is user
