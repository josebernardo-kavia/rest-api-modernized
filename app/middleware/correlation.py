"""Correlation ID middleware to improve request tracing across services."""

from __future__ import annotations

import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Injects a correlation ID into each request/response via `X-Request-Id`."""

    header_name: str = "X-Request-Id"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = request.headers.get(self.header_name) or str(uuid.uuid4())

        # Expose to downstream handlers.
        request.state.correlation_id = correlation_id

        response = await call_next(request)
        response.headers[self.header_name] = correlation_id
        return response
