from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response model"""

    data: List[T]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


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

    errors: Optional[List[ErrorField]] = None
    """Field-level problems. Populated only for validation errors (422)."""
