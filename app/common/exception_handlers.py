"""Centralized exception handling for the API.

All handlers return RFC7807 "Problem Details" payloads using the media type:
`application/problem+json`.

Attach these handlers to both the root `app` and the prefixed `api_app` so behavior
is consistent for all endpoints.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import DBAPIError, IntegrityError, SQLAlchemyError
from starlette.responses import JSONResponse

from app.common.errors import ProblemDetail
from app.domain.errors import NotFoundError

logger = logging.getLogger(__name__)

PROBLEM_JSON_MEDIA_TYPE = "application/problem+json"


def _instance_from_request(request: Request) -> str:
    """Return a stable RFC7807 `instance` value based on request path."""
    # Include only the path (not query) to avoid leaking secrets and keep instances stable.
    return request.url.path


def _problem_response(problem: ProblemDetail, *, headers: Optional[Dict[str, str]] = None) -> JSONResponse:
    """Return a JSONResponse using RFC7807 media type."""
    return JSONResponse(
        status_code=problem.status,
        content=problem.model_dump(exclude_none=True),
        media_type=PROBLEM_JSON_MEDIA_TYPE,
        headers=headers,
    )


# PUBLIC_INTERFACE
def register_exception_handlers(app: Any) -> None:
    """PUBLIC_INTERFACE: Register global exception handlers on the given FastAPI app."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        # FastAPI uses HTTPException.detail as any JSON-able type; we coerce to string
        # for RFC7807 `detail` to keep responses consistent.
        detail_str = None
        if exc.detail is not None:
            detail_str = str(exc.detail)

        problem = ProblemDetail(
            type="about:blank",
            title=_title_from_status(exc.status_code),
            status=int(exc.status_code),
            detail=detail_str,
            instance=_instance_from_request(request),
        )
        # Preserve provided headers (e.g., WWW-Authenticate) if any.
        headers = {str(k): str(v) for k, v in (exc.headers or {}).items()} if exc.headers else None
        return _problem_response(problem, headers=headers)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Convert FastAPI validation errors to RFC7807 with `errors` extension member.
        problem = ProblemDetail(
            type="https://example.com/problems/validation-error",
            title="Validation error",
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Request validation failed.",
            instance=_instance_from_request(request),
            errors=exc.errors(),
        )
        return _problem_response(problem)

    @app.exception_handler(NotFoundError)
    async def not_found_exception_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        problem = ProblemDetail(
            type="about:blank",
            title="Not Found",
            status=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
            instance=_instance_from_request(request),
        )
        return _problem_response(problem)

    @app.exception_handler(PermissionError)
    async def permission_error_handler(request: Request, exc: PermissionError) -> JSONResponse:
        problem = ProblemDetail(
            type="about:blank",
            title="Forbidden",
            status=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
            instance=_instance_from_request(request),
        )
        return _problem_response(problem)

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        # Integrity errors are typically conflicts/constraint violations.
        logger.info("IntegrityError at %s: %s", request.url.path, exc, exc_info=True)
        problem = ProblemDetail(
            type="about:blank",
            title="Conflict",
            status=status.HTTP_409_CONFLICT,
            detail="A database constraint was violated.",
            instance=_instance_from_request(request),
        )
        return _problem_response(problem)

    @app.exception_handler(DBAPIError)
    async def dbapi_error_handler(request: Request, exc: DBAPIError) -> JSONResponse:
        # DBAPIError indicates lower-level DB failures; do not expose details.
        logger.error("DBAPIError at %s: %s", request.url.path, exc, exc_info=True)
        problem = ProblemDetail(
            type="about:blank",
            title="Internal Server Error",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred.",
            instance=_instance_from_request(request),
        )
        return _problem_response(problem)

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        # Catch remaining SQLAlchemy exceptions.
        logger.error("SQLAlchemyError at %s: %s", request.url.path, exc, exc_info=True)
        problem = ProblemDetail(
            type="about:blank",
            title="Internal Server Error",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred.",
            instance=_instance_from_request(request),
        )
        return _problem_response(problem)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Last-resort handler. Do not leak exception details.
        logger.error("Unhandled exception at %s: %s", request.url.path, exc, exc_info=True)
        problem = ProblemDetail(
            type="about:blank",
            title="Internal Server Error",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
            instance=_instance_from_request(request),
        )
        return _problem_response(problem)


def _title_from_status(status_code: int) -> str:
    """Map common status codes to a stable RFC7807 title."""
    titles: Dict[int, str] = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        409: "Conflict",
        422: "Validation error",
        500: "Internal Server Error",
        503: "Service Unavailable",
    }
    return titles.get(int(status_code), "Error")
