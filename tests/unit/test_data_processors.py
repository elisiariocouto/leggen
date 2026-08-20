"""Tests for raw transaction processing.

The date handling here exists because EnableBanking marks all three of
``booking_date``, ``value_date`` and ``transaction_date`` optional, and ASPSPs
differ in which they populate — a Belfius account that omitted the first two
used to abort its whole sync (issue #66).
"""

from loguru import logger

from leggen.services.data_processors import process_transactions

ACCOUNT_INFO = {"institution_id": "BELFIUS_GKCCBEBB", "iban": "BE31063XXXXXXXXX"}


def _wrap(*transactions):
    return {"transactions": list(transactions)}


def _transaction(**overrides):
    base = {
        "transaction_id": "txn-123",
        "entry_reference": "ref-123",
        "booking_date": "2025-09-01",
        "value_date": "2025-09-01",
        "transaction_amount": {"amount": "-10.50", "currency": "EUR"},
        "remittance_information": ["Coffee Shop Payment"],
        "status": "BOOK",
    }
    base.update(overrides)
    return base


class TestDateFallback:
    """All three EnableBanking date fields are optional."""

    def test_transaction_date_only(self):
        """The issue #66 shape: neither booking_date nor value_date present."""
        raw = _transaction(booking_date=None, value_date=None)
        raw["transaction_date"] = "2025-09-03"

        processed, skipped = process_transactions("acc-1", ACCOUNT_INFO, _wrap(raw))

        assert skipped == 0
        assert processed[0]["transactionDate"] == "2025-09-03T00:00:00"

    def test_earliest_of_all_three_wins(self):
        raw = _transaction(booking_date="2025-09-05", value_date="2025-09-02")
        raw["transaction_date"] = "2025-09-09"

        processed, skipped = process_transactions("acc-1", ACCOUNT_INFO, _wrap(raw))

        assert skipped == 0
        assert processed[0]["transactionDate"] == "2025-09-02T00:00:00"

    def test_booking_date_only_still_works(self):
        raw = _transaction(value_date=None)

        processed, _ = process_transactions("acc-1", ACCOUNT_INFO, _wrap(raw))

        assert processed[0]["transactionDate"] == "2025-09-01T00:00:00"


class TestSkipsAreNotFatal:
    """One unparseable transaction must not discard the account's batch."""

    def test_dateless_transaction_is_skipped(self):
        bad = _transaction(transaction_id="txn-bad", booking_date=None, value_date=None)

        processed, skipped = process_transactions(
            "acc-1", ACCOUNT_INFO, _wrap(bad, _transaction())
        )

        assert skipped == 1
        assert [t["transactionId"] for t in processed] == ["txn-123"]

    def test_missing_identifiers_are_skipped(self):
        bad = _transaction(transaction_id=None, entry_reference=None)

        processed, skipped = process_transactions(
            "acc-1", ACCOUNT_INFO, _wrap(bad, _transaction())
        )

        assert skipped == 1
        assert len(processed) == 1

    def test_malformed_date_is_skipped(self):
        bad = _transaction(transaction_id="txn-bad", booking_date="not-a-date")

        processed, skipped = process_transactions(
            "acc-1", ACCOUNT_INFO, _wrap(bad, _transaction())
        )

        assert skipped == 1
        assert [t["transactionId"] for t in processed] == ["txn-123"]

    def test_raw_payload_is_logged_for_reporting(self):
        """The raw payload must reach the logs so users can report it upstream."""
        bad = _transaction(booking_date=None, value_date=None)
        bad["remittance_information"] = ["Belfius groceries"]

        messages: list[str] = []
        sink_id = logger.add(messages.append, level="ERROR")
        try:
            process_transactions("acc-1", ACCOUNT_INFO, _wrap(bad))
        finally:
            logger.remove(sink_id)

        logged = "".join(messages)
        assert "Skipping unparseable transaction" in logged
        assert "Belfius groceries" in logged

    def test_all_good_transactions_report_no_skips(self):
        processed, skipped = process_transactions(
            "acc-1", ACCOUNT_INFO, _wrap(_transaction(), _transaction())
        )

        assert (len(processed), skipped) == (2, 0)

    def test_empty_payload(self):
        assert process_transactions("acc-1", ACCOUNT_INFO, {}) == ([], 0)
