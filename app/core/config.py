"""Application configuration loaded from environment variables."""

from __future__ import annotations

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = Field(default="rest-api-modernized", description="Human-friendly service name.")
    APP_VERSION: str = Field(default="0.1.0", description="Service version string.")
    API_PREFIX: str = Field(default="/api", description="Base path prefix for API routes.")
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default_factory=list,
        description=(
            "Allowed CORS origins for the backend. "
            "Provide as a JSON array (recommended) or a comma-separated string."
        ),
    )
    LOG_LEVEL: str = Field(default="INFO", description="Python logging level (e.g., INFO, DEBUG).")

    # Database
    DATABASE_URL: str = Field(
        default="",
        description="Database connection URL (configure in environment).",
    )

    # OIDC / Keycloak-compatible JWT validation
    OIDC_ISSUER_URL: str = Field(
        default="",
        description=(
            "OIDC issuer base URL. Example: "
            "https://keycloak.example.com/realms/<realm>"
        ),
    )
    OIDC_AUDIENCE: str = Field(
        default="",
        description=(
            "Expected access token audience ('aud'). "
            "For Keycloak this is often 'account' or the client-id depending on configuration."
        ),
    )
    OIDC_CLIENT_ID: str = Field(
        default="",
        description=(
            "Client id of this API (resource). Used for role extraction from "
            "resource_access[client_id].roles."
        ),
    )
    OIDC_CACHE_TTL_SECONDS: int = Field(
        default=300,
        ge=30,
        le=86400,
        description="TTL (seconds) for OIDC discovery + JWKS cache.",
    )

    # Back-compat placeholders (deprecated; kept to avoid breaking earlier scaffolding)
    KEYCLOAK_ISSUER_URL: str = Field(
        default="",
        description="DEPRECATED (use OIDC_ISSUER_URL).",
    )
    KEYCLOAK_AUDIENCE: str = Field(
        default="",
        description="DEPRECATED (use OIDC_AUDIENCE).",
    )


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Return a cached Settings instance (simple singleton for app lifetime)."""
    # Import-time singleton: good enough for this stage; can be replaced with lru_cache if desired.
    global _SETTINGS  # noqa: PLW0603
    try:
        return _SETTINGS
    except NameError:
        _SETTINGS = Settings()  # type: ignore[misc]
        return _SETTINGS
