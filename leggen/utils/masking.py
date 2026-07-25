"""Helpers for masking secrets in API responses and resolving them on update.

Settings endpoints never return stored secrets; they return MASK instead.
Clients may echo MASK back on update to mean "keep the current value".
"""

from typing import Optional

MASK = "***"


class MaskedSecretError(ValueError):
    """A client echoed back the mask but no secret is stored to keep.

    Distinct from a plain ValueError so callers can surface this message to
    the client without risking an unrelated error's text leaking.
    """


def mask_secret(value: Optional[str]) -> str:
    """Return the mask placeholder if a secret is set, empty string otherwise."""
    return MASK if value else ""


def resolve_secret(incoming: str, stored: Optional[str], field_name: str) -> str:
    """Resolve a secret submitted by a client against the stored value.

    An incoming MASK means the client is echoing back a masked read and wants
    to keep the currently stored secret.

    Raises:
        MaskedSecretError: If the client sent MASK but no secret is stored.
    """
    if incoming != MASK:
        return incoming
    if not stored:
        raise MaskedSecretError(
            f"Received masked placeholder for {field_name}, "
            "but no existing value is configured"
        )
    return stored
