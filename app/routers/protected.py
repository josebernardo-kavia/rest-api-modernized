"""Protected example endpoints (requires valid OIDC access token)."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends

from app.auth.dependencies import AuthenticatedUser, get_current_user, require_roles
from app.common.errors import COMMON_ERROR_RESPONSES

router = APIRouter(tags=["Auth"])


@router.get(
    "/protected",
    summary="Protected example endpoint",
    description="Returns basic identity information for the current authenticated user.",
    operation_id="protected_example",
    responses=COMMON_ERROR_RESPONSES,
)
async def protected_example(user: AuthenticatedUser = Depends(get_current_user)) -> Dict[str, Any]:
    """
    PUBLIC_INTERFACE
    Example protected endpoint.

    Requires:
        Authorization: Bearer <access_token>

    Returns:
        A JSON object with user identity and roles extracted from the token.
    """
    return {
        "subject": user.subject,
        "username": user.username,
        "email": user.email,
        "roles": sorted(user.roles),
        "issuer": user.issuer,
    }


@router.get(
    "/protected/admin",
    summary="Protected admin-only example endpoint",
    description="Requires a valid token AND at least one of the configured admin roles.",
    operation_id="protected_admin_example",
    responses=COMMON_ERROR_RESPONSES,
)
async def protected_admin_example(
    user: AuthenticatedUser = Depends(require_roles(["admin", "realm-admin"])),
) -> Dict[str, Any]:
    """
    PUBLIC_INTERFACE
    Example role-protected endpoint.

    Notes:
        The required role names here are examples. Adjust to your Keycloak realm/client roles.

    Returns:
        A JSON object confirming authorization.
    """
    return {"ok": True, "subject": user.subject, "roles": sorted(user.roles)}
