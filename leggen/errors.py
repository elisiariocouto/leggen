"""Domain errors raised by services and repositories.

These describe *what* went wrong in the domain, with no HTTP imports, so any
layer may raise them. The API turns them into responses in
`leggen.api.errors`; the status codes below are the mapping it uses.
"""


class LeggenError(Exception):
    """Base for domain errors that map onto an HTTP response."""

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


class CategoryExistsError(ConflictError):
    """A category with the requested name already exists."""

    code = "CATEGORY_EXISTS"
