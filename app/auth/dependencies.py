"""FastAPI auth dependencies for Keycloak-compatible JWT validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, Optional, Sequence, Set

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError

from app.auth.oidc import fetch_jwks
from app.core.config import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    """Represents the authenticated principal extracted from an access token."""

    subject: str
    username: Optional[str]
    email: Optional[str]
    issuer: str
    audience: Optional[str]
    roles: FrozenSet[str] = field(default_factory=frozenset)
    raw_claims: Dict[str, Any] = field(default_factory=dict)


def _resolve_audience(settings: Settings) -> str:
    """Resolve audience from current settings, allowing deprecated KEYCLOAK_* fallbacks."""
    aud = (settings.OIDC_AUDIENCE or "").strip()
    if not aud:
        aud = (settings.KEYCLOAK_AUDIENCE or "").strip()
    return aud


def _extract_roles_from_keycloak_claims(claims: Dict[str, Any], *, client_id: str) -> Set[str]:
    """
    Extract roles from Keycloak-standard claims.

    - realm roles: realm_access.roles
    - client roles: resource_access[client_id].roles
    """
    roles: Set[str] = set()

    realm_access = claims.get("realm_access")
    if isinstance(realm_access, dict):
        realm_roles = realm_access.get("roles")
        if isinstance(realm_roles, list):
            roles |= {str(r) for r in realm_roles if isinstance(r, (str, int))}

    resource_access = claims.get("resource_access")
    if isinstance(resource_access, dict) and client_id:
        client_access = resource_access.get(client_id)
        if isinstance(client_access, dict):
            client_roles = client_access.get("roles")
            if isinstance(client_roles, list):
                roles |= {str(r) for r in client_roles if isinstance(r, (str, int))}

    # Some deployments also use "roles" or "groups"; include lightly (best effort).
    direct_roles = claims.get("roles")
    if isinstance(direct_roles, list):
        roles |= {str(r) for r in direct_roles if isinstance(r, (str, int))}

    return roles


def _get_signing_key_from_jwks(token: str, jwks: Dict[str, Any]) -> Any:
    """
    Resolve a public key for the JWT `kid` using JWKS.

    We use PyJWT's PyJWKClient in-memory by feeding it a JWKS URL is not possible here,
    so we construct keys directly from the JWKS dict.
    """
    # PyJWT exposes a JWK set helper internally via PyJWKClient, but it expects a URL fetcher.
    # Instead, we parse the header to find kid and select the matching JWK.
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")
    if not kid:
        raise InvalidTokenError("JWT header missing 'kid'.")

    keys = jwks.get("keys")
    if not isinstance(keys, list):
        raise InvalidTokenError("JWKS missing 'keys' list.")

    for jwk_dict in keys:
        if isinstance(jwk_dict, dict) and jwk_dict.get("kid") == kid:
            return jwt.algorithms.RSAAlgorithm.from_jwk(jwk_dict)

    raise InvalidTokenError("No matching JWK found for token kid.")


# PUBLIC_INTERFACE
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> AuthenticatedUser:
    """
    PUBLIC_INTERFACE
    Validate a Bearer access token (RS256) against OIDC issuer JWKS and return the authenticated user.

    This dependency is Keycloak-compatible:
    - Uses OIDC discovery -> jwks_uri -> JWKS keys
    - Verifies RS256 signature and standard claims
    - Extracts realm/client roles from Keycloak claim conventions

    Args:
        credentials: HTTP Authorization bearer credentials extracted by FastAPI.
        settings: Application settings.

    Returns:
        AuthenticatedUser

    Raises:
        HTTPException(401): If token is missing/invalid.
    """
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token.",
        )

    token = credentials.credentials

    issuer = (settings.OIDC_ISSUER_URL or settings.KEYCLOAK_ISSUER_URL or "").rstrip("/")
    if not issuer:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server auth misconfiguration: OIDC_ISSUER_URL is not set.",
        )

    audience = _resolve_audience(settings)
    if not audience:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server auth misconfiguration: OIDC_AUDIENCE is not set.",
        )

    # Fetch/cached JWKS and validate signature + claims
    try:
        jwks = await fetch_jwks(settings=settings)
        signing_key = _get_signing_key_from_jwks(token, jwks)

        claims: Dict[str, Any] = jwt.decode(
            token,
            key=signing_key,
            algorithms=["RS256"],
            audience=audience,
            issuer=issuer,
            options={
                # Require standard registered claims typical for access tokens
                "require": ["exp", "iat", "iss", "sub"],
            },
        )
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid access token: {exc}",
        ) from exc
    except RuntimeError as exc:
        # RuntimeError comes from discovery/JWKS fetch issues; treat as auth service unavailable.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Auth metadata unavailable: {exc}",
        ) from exc

    subject = str(claims.get("sub", ""))
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject.")

    preferred_username = claims.get("preferred_username")
    username = str(preferred_username) if preferred_username is not None else None
    email_val = claims.get("email")
    email = str(email_val) if email_val is not None else None

    client_id = (settings.OIDC_CLIENT_ID or "").strip()
    roles = _extract_roles_from_keycloak_claims(claims, client_id=client_id)

    aud_claim = claims.get("aud")
    aud_str = None
    if isinstance(aud_claim, str):
        aud_str = aud_claim
    elif isinstance(aud_claim, list) and aud_claim:
        aud_str = str(aud_claim[0])

    return AuthenticatedUser(
        subject=subject,
        username=username,
        email=email,
        issuer=str(claims.get("iss", issuer)),
        audience=aud_str,
        roles=frozenset(sorted(roles)),
        raw_claims=claims,
    )


# PUBLIC_INTERFACE
def require_roles(required: Sequence[str]) -> Any:
    """
    PUBLIC_INTERFACE
    Create a dependency that requires the current user to have at least one of the given roles.

    Notes:
        This is an OR-check by design (any-of). For all-of semantics, wrap multiple calls or extend.

    Args:
        required: A list/tuple of role names.

    Returns:
        A FastAPI dependency callable that yields the AuthenticatedUser if authorized.

    Raises:
        HTTPException(403): If user lacks required roles.
    """
    required_set = {r for r in required if isinstance(r, str) and r.strip()}
    required_frozen: FrozenSet[str] = frozenset(required_set)

    async def _dependency(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if not required_frozen:
            return user

        if user.roles.intersection(required_frozen):
            return user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required role(s): {sorted(required_frozen)}",
        )

    return _dependency
