"""Domain-layer exceptions."""

from __future__ import annotations


class NotFoundError(Exception):
    """Raised when a requested entity does not exist."""
