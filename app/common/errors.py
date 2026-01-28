"""Common error responses and Problem Details model.

This module standardizes error payloads across the API using an RFC7807-compatible
"Problem Details" envelope and reusable OpenAPI response docs.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProblemDetail(BaseModel):
    """
    RFC7807 Problem Details response body.

    Notes:
        We keep the core RFC7807 fields and add an optional `errors` extension member
        for validation / field-level details.
    """

    type: str = Field(
        default="about:blank",
        description="A URI reference that identifies the problem type.",
        examples=["https://example.com/problems/validation-error"],
    )
    title: str = Field(
        ...,
        description="Short, human-readable summary of the problem type.",
        examples=["Validation error"],
    )
    status: int = Field(..., description="HTTP status code.", examples=[422])
    detail: Optional[str] = Field(
        default=None,
        description="Human-readable explanation specific to this occurrence.",
        examples=["Request body validation failed."],
    )
    instance: Optional[str] = Field(
        default=None,
        description="A URI reference that identifies the specific occurrence (request path).",
        examples=["/api/projects"],
    )
    errors: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description=(
            "Optional extension member containing machine-readable error details, "
            "e.g. validation failures. Shape is compatible with FastAPI/Pydantic error objects."
        ),
        examples=[
            [
                {
                    "loc": ["body", "name"],
                    "msg": "Field required",
                    "type": "missing",
                }
            ]
        ],
    )


# PUBLIC_INTERFACE
def problem_detail_example() -> ProblemDetail:
    """PUBLIC_INTERFACE: Return a representative ProblemDetail example for OpenAPI docs."""
    return ProblemDetail(
        type="about:blank",
        title="Bad Request",
        status=400,
        detail="The request could not be processed.",
        instance="/api/example",
    )


# PUBLIC_INTERFACE
def validation_problem_example() -> ProblemDetail:
    """PUBLIC_INTERFACE: Return a representative validation error example for OpenAPI docs."""
    return ProblemDetail(
        type="https://example.com/problems/validation-error",
        title="Validation error",
        status=422,
        detail="Request validation failed.",
        instance="/api/projects",
        errors=[
            {"loc": ["body", "name"], "msg": "Field required", "type": "missing"},
        ],
    )


def _problem_content_schema() -> Dict[str, Any]:
    """OpenAPI content schema for application/problem+json."""
    # FastAPI's OpenAPI uses `content` for media types. By specifying the model in schema,
    # Swagger/ReDoc will display the correct problem+json payload.
    return {
        "application/problem+json": {
            "schema": ProblemDetail.model_json_schema(),
        }
    }


def _problem_content_with_example(example: ProblemDetail) -> Dict[str, Any]:
    """OpenAPI content schema for application/problem+json with a concrete example."""
    return {
        "application/problem+json": {
            "schema": ProblemDetail.model_json_schema(),
            "example": example.model_dump(exclude_none=True),
        }
    }


# Common reusable response documentation blocks for FastAPI.
# These are intended for `responses=...` in route decorators (documentation only).
COMMON_ERROR_RESPONSES: Dict[int, Dict[str, Any]] = {
    400: {
        "description": "Bad Request",
        "content": _problem_content_with_example(problem_detail_example()),
    },
    401: {
        "description": "Unauthorized",
        "content": _problem_content_with_example(
            ProblemDetail(
                type="about:blank",
                title="Unauthorized",
                status=401,
                detail="Missing Bearer token.",
                instance="/api/resource",
            )
        ),
    },
    403: {
        "description": "Forbidden",
        "content": _problem_content_with_example(
            ProblemDetail(
                type="about:blank",
                title="Forbidden",
                status=403,
                detail="Missing required role(s): ['admin']",
                instance="/api/resource",
            )
        ),
    },
    404: {
        "description": "Not Found",
        "content": _problem_content_with_example(
            ProblemDetail(
                type="about:blank",
                title="Not Found",
                status=404,
                detail="Resource not found.",
                instance="/api/resource/123",
            )
        ),
    },
    409: {
        "description": "Conflict",
        "content": _problem_content_schema(),
    },
    422: {
        "description": "Validation Error",
        "content": _problem_content_with_example(validation_problem_example()),
    },
    500: {
        "description": "Internal Server Error",
        "content": _problem_content_schema(),
    },
    503: {
        "description": "Service Unavailable",
        "content": _problem_content_schema(),
    },
}
