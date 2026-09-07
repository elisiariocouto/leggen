"""Domain errors raised by services and repositories.

These describe *what* went wrong in the domain, with no HTTP imports, so any
layer may raise them. The API turns them into responses in
`leggen.api.errors`; the status codes below are the mapping it uses.
"""


def describe_exception(exc: BaseException) -> str:
    """Return a human-readable description of an exception.

    Some exceptions carry no message — notably httpx timeouts, whose ``str()``
    is empty — which would otherwise be logged as a bare "failed: " with no
    indication of the cause. Fall back to the class name so the failure is
    always identifiable, and qualify it with the message when there is one.
    """
    detail = str(exc).strip()
    if not detail:
        return type(exc).__name__
    return f"{type(exc).__name__}: {detail}"


class LeggenError(Exception):
    """Base for domain errors that map onto an HTTP response."""

    status_code: int = 500
    code: str = "INTERNAL_ERROR"

    headers: dict[str, str] | None = None
    """Response headers the error requires, e.g. WWW-Authenticate on a 401."""

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


class UnsupportedDatabaseVersionError(LeggenError):
    """The database predates the oldest schema this version can migrate.

    Migrations older than the 2025.9.22 baseline were retired; a database that
    never had them applied cannot be upgraded directly, because the baseline
    schema is created with CREATE TABLE IF NOT EXISTS and would silently leave
    the legacy tables in place.
    """

    code = "UNSUPPORTED_DATABASE_VERSION"


class AuthenticationError(LeggenError):
    """The request carried no usable credentials."""

    status_code = 401
    code = "INVALID_CREDENTIALS"
    headers = {"WWW-Authenticate": "Bearer"}


class TokenExpiredError(AuthenticationError):
    """The bearer token was well-formed and correctly signed, but has lapsed.

    Distinguished from a plainly invalid token so the frontend can tell the
    user their session expired and send them back to the login form, rather
    than reporting a credential failure they cannot act on.
    """

    code = "TOKEN_EXPIRED"


class NotificationNotEnabledError(LeggenError):
    """The notification service is missing credentials or switched off.

    Distinct from a delivery failure: nothing was attempted, and the fix is a
    configuration change rather than a retry.
    """

    status_code = 400
    code = "NOTIFICATION_NOT_ENABLED"


class UpstreamServiceError(LeggenError):
    """A third-party service the request depends on failed or was unreachable.

    The request itself was well-formed, so this is a 502 rather than a 4xx: the
    caller can retry once the upstream recovers.
    """

    status_code = 502
    code = "UPSTREAM_ERROR"
