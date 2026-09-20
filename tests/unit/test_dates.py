"""Tests for the shared timestamp and day parsers."""

from datetime import UTC, date, datetime, timedelta, timezone

import pytest

from leggen.utils.dates import parse_datetime, parse_day


@pytest.mark.unit
class TestParseDatetime:
    def test_naive_is_read_as_utc(self):
        assert parse_datetime("2026-03-24T10:00:00") == datetime(
            2026, 3, 24, 10, tzinfo=UTC
        )

    def test_offsets_and_zulu_are_normalised_to_utc(self):
        expected = datetime(2026, 3, 24, 9, tzinfo=UTC)
        assert parse_datetime("2026-03-24T10:00:00+01:00") == expected
        assert parse_datetime("2026-03-24T09:00:00Z") == expected
        assert parse_datetime("2026-03-24T09:00:00Z").tzinfo == UTC

    def test_unparseable_values_are_none(self):
        assert parse_datetime(None) is None
        assert parse_datetime("") is None
        assert parse_datetime("tomorrow") is None


@pytest.mark.unit
class TestParseDay:
    def test_reads_days_and_timestamps(self):
        assert parse_day("2026-03-24") == date(2026, 3, 24)
        assert parse_day("2026-03-24T23:30:00") == date(2026, 3, 24)

    def test_keeps_the_written_day_not_the_utc_day(self):
        late = datetime(2026, 3, 24, 23, 30, tzinfo=timezone(timedelta(hours=-3)))
        assert parse_day(late.isoformat()) == date(2026, 3, 24)

    def test_unparseable_values_are_none(self):
        assert parse_day(None) is None
        assert parse_day("March") is None
