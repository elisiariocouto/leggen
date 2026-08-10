"""Tests for the transaction repository."""

import pytest

from leggen.repositories import TransactionRepository


def _make_transaction(**overrides):
    transaction = {
        "accountId": "IBAN1",
        "transactionId": "tx-1",
        "internalTransactionId": "internal-1",
        "institutionId": "Test Bank",
        "iban": "IBAN1",
        "transactionDate": "2026-07-01T10:00:00",
        "description": "Coffee",
        "transactionValue": -3.5,
        "transactionCurrency": "EUR",
        "transactionStatus": "PNDG",
        "rawTransaction": {"entry_reference": "ref-1"},
    }
    transaction.update(overrides)
    return transaction


@pytest.mark.unit
class TestTransactionRepositoryPersist:
    """Test new/updated/unchanged accounting in persist()."""

    def test_new_transaction_counted_as_new(self, mock_db_path):
        repo = TransactionRepository()

        new_transactions, updated_count = repo.persist("IBAN1", [_make_transaction()])

        assert len(new_transactions) == 1
        assert updated_count == 0

    def test_unchanged_transaction_not_counted(self, mock_db_path):
        repo = TransactionRepository()
        repo.persist("IBAN1", [_make_transaction()])

        new_transactions, updated_count = repo.persist("IBAN1", [_make_transaction()])

        assert new_transactions == []
        assert updated_count == 0

    def test_changed_transaction_counted_as_updated(self, mock_db_path):
        repo = TransactionRepository()
        repo.persist("IBAN1", [_make_transaction()])

        # Pending transaction becomes booked on a later sync
        new_transactions, updated_count = repo.persist(
            "IBAN1", [_make_transaction(transactionStatus="BOOK")]
        )

        assert new_transactions == []
        assert updated_count == 1
        stored = repo.get_transaction_by_id("IBAN1", "tx-1")
        assert stored is not None
        assert stored["transactionStatus"] == "BOOK"

    def test_mismatched_account_id_rejected(self, mock_db_path):
        """Rows for another account must fail fast, not write under the
        wrong primary key while reporting success for account_id."""
        repo = TransactionRepository()

        with pytest.raises(ValueError, match="IBAN2"):
            repo.persist("IBAN1", [_make_transaction(accountId="IBAN2")])

    def test_duplicate_id_in_batch_counted_once(self, mock_db_path):
        """The same transactionId twice in one batch (e.g. a pending and a
        booked entry in one fetch) is one insert plus one update, never two
        inserts — double-counting meant duplicate notifications."""
        repo = TransactionRepository()

        new_transactions, updated_count = repo.persist(
            "IBAN1",
            [
                _make_transaction(transactionStatus="PNDG"),
                _make_transaction(transactionStatus="BOOK"),
            ],
        )

        assert len(new_transactions) == 1
        assert updated_count == 1
