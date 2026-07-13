"""Structured error-response handlers for the FastAPI application.

Registered in ``create_app()`` to ensure that clients never
receive stack traces, SQL errors, internal file paths, or
provider exception details.
"""

from __future__ import annotations

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.observability.logger import get_logger

logger = get_logger(__name__)


def _build_error(
    error: str,
    message: str,
    status_code: int = 500,
    *,
    details: object = None,
) -> JSONResponse:
    body: dict[str, object] = {
        "error": error,
        "message": message,
    }
    if details is not None:
        body["details"] = details
    return JSONResponse(status_code=status_code, content=body)


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Return structured 422 for Pydantic validation failures."""
    logger.warning(
        "validation_error",
        path=str(request.url),
        method=request.method,
        errors=exc.errors(),
    )
    return _build_error(
        error="validation_error",
        message="Request validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=exc.errors(),
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Return structured error for HTTPException (including 404, 405, etc)."""
    detail = exc.detail
    # pydantic may return a dict/list detail; normalise to string
    if isinstance(detail, dict):
        message = detail.get("message", str(detail))
        error = detail.get("error", "http_error")
    else:
        message = str(detail) if detail else "HTTP error"
        error = "http_error"
    return _build_error(
        error=error,
        message=message,
        status_code=exc.status_code,
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Catch-all: return 500 with zero internal details exposed."""
    logger.exception(
        "unhandled_exception",
        path=str(request.url),
        method=request.method,
    )
    return _build_error(
        error="internal_error",
        message="An unexpected error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
