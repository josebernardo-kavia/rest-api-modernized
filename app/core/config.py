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

    # Placeholders for future steps (DB and auth).
    DATABASE_URL: str = Field(
        default="",
        description="Database connection URL (placeholder; configure in environment).",
    )
    KEYCLOAK_ISSUER_URL: str = Field(
        default="",
        description="Keycloak issuer URL used to validate JWTs (placeholder).",
    )
    KEYCLOAK_AUDIENCE: str = Field(
        default="",
        description="Expected JWT audience for this API (placeholder).",
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
