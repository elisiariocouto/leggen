"""Domain errors and the exception handlers that render them.

Every error leaving the API is shaped by one of the handlers registered in
`register_exception_handlers`, so clients see a single envelope
(`leggen.api.models.common.ErrorResponse`) regardless of where the failure
came from: a deliberate `HTTPException`, a `LeggenError` raised deep in a
service, request validation, or an unhandled crash.
"""

from typing import TYPE_CHECKING, Any

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException

from leggen.api.models.common import ErrorField, ErrorResponse

if TYPE_CHECKING:
    from starlette.requests import Request


class LeggenError(Exception):
    """Base for domain errors that map onto an HTTP response.

    Services and repositories raise these to signal *what* went wrong without
    importing HTTP concerns; the handler below turns them into responses.
    """

    status_code: int = 500
    code: str = "INTERNAL_ERROR"

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class NotFoundError(LeggenError):
    """The requested resource does not exist."""

    status_code = 404
    code = "NOT_FOUND"


class ConflictError(LeggenError):
    """The request conflicts with the current state of the resource."""

    status_code = 409
    code = "CONFLICT"


# Fallback codes for errors raised as plain HTTPExceptions, which carry a
# status but no code of their own.
_STATUS_CODES: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
    502: "UPSTREAM_ERROR",
    503: "SERVICE_UNAVAILABLE",
}


def code_for_status(status_code: int) -> str:
    """Map an HTTP status onto a machine-readable error code."""
    return _STATUS_CODES.get(status_code, "HTTP_ERROR")


def error_response(
    status_code: int,
    detail: str,
    code: str | None = None,
    errors: list[ErrorField] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Render the unified error envelope."""
    body = ErrorResponse(
        detail=detail,
        code=code or code_for_status(status_code),
        status=status_code,
        errors=errors,
    )
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(body, exclude_none=True),
        headers=headers,
    )


async def leggen_error_handler(request: "Request", exc: LeggenError) -> JSONResponse:
    """Render a domain error using the status and code it declares."""
    return error_response(exc.status_code, exc.detail, code=exc.code)


async def http_exception_handler(
    request: "Request", exc: StarletteHTTPException
) -> JSONResponse:
    """Render HTTPExceptions, including Starlette's own 404/405 for unknown routes."""
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    # Headers matter here: the auth dependency sets WWW-Authenticate on its 401.
    return error_response(
        exc.status_code, detail, headers=getattr(exc, "headers", None)
    )


async def validation_exception_handler(
    request: "Request", exc: RequestValidationError
) -> JSONResponse:
    """Render request validation failures with a string detail plus field errors.

    FastAPI's default puts a list in `detail`; we keep `detail` a string and
    move the per-field information into `errors`.
    """
    errors = [
        ErrorField(
            field=".".join(str(part) for part in err.get("loc", ())),
            message=str(err.get("msg", "Invalid value")),
            type=str(err.get("type", "value_error")),
        )
        # Only loc/msg/type are copied. Pydantic also reports `input` (the
        # submitted value) and `ctx`, which would echo back user secrets such
        # as an S3 key rejected by validation.
        for err in exc.errors()
    ]

    if len(errors) == 1:
        detail = f"{errors[0].field}: {errors[0].message}"
    else:
        detail = f"Request validation failed ({len(errors)} problems)."

    return error_response(422, detail, errors=errors)


async def unhandled_exception_handler(
    request: "Request", exc: Exception
) -> JSONResponse:
    """Render anything that escaped a route as a sanitized JSON 500.

    Without this, Starlette returns a plain-text body that no client can parse.
    The exception itself only ever reaches the log.
    """
    logger.exception(
        f"Unhandled error on {request.method} {request.url.path}: {exc}",
    )
    return error_response(500, "Internal server error.")


def register_exception_handlers(app: FastAPI) -> None:
    """Register the handlers that give every error response one shape."""
    handlers: list[tuple[Any, Any]] = [
        (LeggenError, leggen_error_handler),
        (StarletteHTTPException, http_exception_handler),
        (RequestValidationError, validation_exception_handler),
        (Exception, unhandled_exception_handler),
    ]
    for exc_class, handler in handlers:
        # Starlette types the registry loosely; the pairs above are consistent.
        app.add_exception_handler(exc_class, handler)
