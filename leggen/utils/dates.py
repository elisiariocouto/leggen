"""Parsing the timestamps this codebase stores and receives.

Two shapes turn up: full timestamps (session validity from EnableBanking,
balance snapshots, sync records) and plain days (transaction dates, API
date ranges). Both are ISO 8601 strings, but with or without a time part,
with or without an offset, and occasionally with a trailing "Z". These two
parsers absorb those differences so callers never repeat the fallbacks.
"""

from datetime import UTC, date, datetime


def parse_datetime(value: str | None) -> datetime | None:
    """An aware datetime in UTC, or None when the value does not parse.

    Timestamps stored without an offset are UTC by convention here.
    """
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def parse_day(value: str | None) -> date | None:
    """The calendar day of a date or timestamp string, or None.

    Only the leading `YYYY-MM-DD` is read when the value carries a time
    part, so a timestamp's day is the day it was written, not its UTC day.
    """
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None
