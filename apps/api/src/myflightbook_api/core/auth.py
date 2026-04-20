from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from myflightbook_api.core.oidc import VerifiedOIDCIdentity
from myflightbook_api.models.user import Identity, User


class AuthStateError(Exception):
    """Base error for local auth state handling."""


class IdentityNotLinkedError(AuthStateError):
    """Raised when a verified OIDC identity has not been linked locally."""


class IdentityConflictError(AuthStateError):
    """Raised when a verified identity conflicts with existing user data."""


class IdentityProvisioningError(AuthStateError):
    """Raised when a verified identity cannot be provisioned locally."""


def _fallback_display_name(identity: VerifiedOIDCIdentity) -> str:
    if identity.display_name:
        return identity.display_name
    if identity.email:
        return identity.email.split("@", 1)[0]
    return f"{identity.provider.value}-{identity.subject}"


async def get_linked_user_for_identity(
    session: AsyncSession,
    verified_identity: VerifiedOIDCIdentity,
) -> User:
    result = await session.execute(
        select(Identity)
        .options(selectinload(Identity.user))
        .where(
            Identity.provider == verified_identity.provider,
            Identity.provider_subject == verified_identity.subject,
        )
    )
    identity = result.scalar_one_or_none()

    if identity is None:
        raise IdentityNotLinkedError("OIDC identity is not linked locally. Call /auth/login first.")
    if identity.user is None or not identity.user.is_active:
        raise IdentityNotLinkedError("The local user account is inactive.")

    return identity.user


async def provision_user_from_identity(
    session: AsyncSession,
    verified_identity: VerifiedOIDCIdentity,
) -> tuple[User, Identity, bool]:
    identity_result = await session.execute(
        select(Identity)
        .options(selectinload(Identity.user))
        .where(
            Identity.provider == verified_identity.provider,
            Identity.provider_subject == verified_identity.subject,
        )
    )
    identity = identity_result.scalar_one_or_none()
    is_new_user = False

    if identity is None:
        user = None
        if verified_identity.email:
            user_result = await session.execute(select(User).where(User.email == verified_identity.email))
            user = user_result.scalar_one_or_none()

        if user is None:
            if not verified_identity.email:
                raise IdentityProvisioningError(
                    "First-time sign-in requires an OIDC token with an email claim."
                )

            user = User(
                email=verified_identity.email,
                display_name=_fallback_display_name(verified_identity),
                given_name=verified_identity.given_name,
                family_name=verified_identity.family_name,
                locale="en-US",
                is_active=True,
            )
            session.add(user)
            await session.flush()
            is_new_user = True

        identity = Identity(
            user=user,
            provider=verified_identity.provider,
            provider_subject=verified_identity.subject,
            email_verified=verified_identity.email_verified,
        )
        session.add(identity)
    else:
        user = identity.user

    if user is None:
        raise IdentityProvisioningError("OIDC identity is missing a linked user record.")
    if not user.is_active:
        raise IdentityProvisioningError("The local user account is inactive.")

    if verified_identity.email and verified_identity.email != user.email:
        email_owner_result = await session.execute(select(User).where(User.email == verified_identity.email))
        email_owner = email_owner_result.scalar_one_or_none()
        if email_owner is not None and email_owner.id != user.id:
            raise IdentityConflictError("Verified email is already attached to another user.")
        user.email = verified_identity.email

    if verified_identity.display_name:
        user.display_name = verified_identity.display_name
    elif not user.display_name:
        user.display_name = _fallback_display_name(verified_identity)

    if verified_identity.given_name is not None:
        user.given_name = verified_identity.given_name
    if verified_identity.family_name is not None:
        user.family_name = verified_identity.family_name

    identity.email_verified = verified_identity.email_verified

    await session.commit()
    await session.refresh(user)
    await session.refresh(identity)
    return user, identity, is_new_user
