from typing import Any, Self

from pydantic import BaseModel


class PaginatedResponse[T](BaseModel):
    """One page of a list, with the arithmetic every paged route needs."""

    data: list[T]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool

    @classmethod
    def build(
        cls, data: list[T], *, total: int, page: int, per_page: int, **extra: Any
    ) -> Self:
        """Assemble a page. An empty list is one empty page, not zero pages,
        so "page 1 of 1" holds for every result set. `extra` carries the
        fields a subclass adds."""
        total_pages = max((total + per_page - 1) // per_page, 1)
        return cls(
            data=data,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
            **extra,
        )


class HealthStatus(BaseModel):
    """Response of the healthy path of /health"""

    status: str
    config_loaded: bool
    version: str


class ErrorField(BaseModel):
    """One field-level validation problem."""

    field: str
    """Dotted path to the offending field, e.g. "query.per_page"."""

    message: str
    """Human-readable description of the problem."""

    type: str
    """Pydantic error type, e.g. "greater_than_equal"."""


class ErrorResponse(BaseModel):
    """Unified error envelope returned by every API error response.

    `detail` is always a plain string, on every status code including 422.
    Clients may rely on that: it is the backward-compatible contract with
    the frontend (`getApiErrorMessage`) and the CLI (`api_client.py`).

    An optional `request_id` could be added here later without breaking
    clients, should log correlation ever become worth the plumbing.
    """

    detail: str
    """Human-readable message, safe to show to the user."""

    code: str
    """Machine-readable error code in SCREAMING_SNAKE_CASE."""

    status: int
    """HTTP status code, duplicated here so bodies are self-describing."""

    errors: list[ErrorField] | None = None
    """Field-level problems. Populated only for validation errors (422)."""
