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


class NotificationNotEnabledError(LeggenError):
    """A notification service was asked to send while switched off or unconfigured."""

    status_code = 400
    code = "NOTIFICATION_NOT_ENABLED"


class NotificationSendError(LeggenError):
    """A notification provider (Discord/Telegram) rejected or failed the send."""

    status_code = 502
    code = "NOTIFICATION_SEND_FAILED"
