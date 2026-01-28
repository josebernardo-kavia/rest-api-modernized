"""Logging configuration utilities for the service."""

from __future__ import annotations

import logging
from typing import Optional


# PUBLIC_INTERFACE
def configure_logging(log_level: str, *, uvicorn_log_level: Optional[str] = None) -> None:
    """
    PUBLIC_INTERFACE
    Configure application logging.

    Args:
        log_level: Logging level for the application (e.g. "INFO", "DEBUG").
        uvicorn_log_level: Optional override for uvicorn's loggers (if needed later).

    Returns:
        None.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    if uvicorn_log_level:
        uvicorn_level = getattr(logging, uvicorn_log_level.upper(), level)
        logging.getLogger("uvicorn").setLevel(uvicorn_level)
        logging.getLogger("uvicorn.error").setLevel(uvicorn_level)
        logging.getLogger("uvicorn.access").setLevel(uvicorn_level)
