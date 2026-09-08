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


@pytest.mark.unit
class TestTransactionRepositoryStatusFilter:
    """Test the status filter shared by get_transactions() and get_count()."""

    @staticmethod
    def _seed(repo: TransactionRepository) -> None:
        repo.persist(
            "IBAN1",
            [
                _make_transaction(transactionId="tx-1", transactionStatus="booked"),
                _make_transaction(transactionId="tx-2", transactionStatus="pending"),
                _make_transaction(transactionId="tx-3", transactionStatus="booked"),
            ],
        )

    def test_filters_transactions_by_status(self, mock_db_path):
        repo = TransactionRepository()
        self._seed(repo)

        pending = repo.get_transactions(status="pending")

        assert [t["transactionId"] for t in pending] == ["tx-2"]

    def test_count_respects_status(self, mock_db_path):
        repo = TransactionRepository()
        self._seed(repo)

        assert repo.get_count(status="booked") == 2
        assert repo.get_count(status="pending") == 1
        assert repo.get_count() == 3

    def test_status_match_is_case_insensitive(self, mock_db_path):
        """Banks are inconsistent about case, so a stored "Pending" must
        still match the "pending" filter."""
        repo = TransactionRepository()
        repo.persist(
            "IBAN1",
            [_make_transaction(transactionId="tx-1", transactionStatus="Pending")],
        )

        assert repo.get_count(status="pending") == 1


@pytest.mark.unit
class TestTransactionRepositorySorting:
    """Test the sort_by/sort_order arguments of get_transactions()."""

    @staticmethod
    def _seed(repo: TransactionRepository) -> None:
        repo.persist(
            "IBAN1",
            [
                _make_transaction(
                    transactionId="tx-old-small",
                    transactionDate="2026-07-01T10:00:00",
                    transactionValue=-5.0,
                    description="Almonds",
                ),
                _make_transaction(
                    transactionId="tx-mid-large",
                    transactionDate="2026-07-02T10:00:00",
                    transactionValue=-100.0,
                    description="Cutlery",
                ),
                _make_transaction(
                    transactionId="tx-new-medium",
                    transactionDate="2026-07-03T10:00:00",
                    transactionValue=-50.0,
                    description="Beans",
                ),
            ],
        )

    def test_defaults_to_newest_first(self, mock_db_path):
        repo = TransactionRepository()
        self._seed(repo)

        rows = repo.get_transactions()

        assert [t["transactionId"] for t in rows] == [
            "tx-new-medium",
            "tx-mid-large",
            "tx-old-small",
        ]

    def test_sorts_by_date_ascending(self, mock_db_path):
        repo = TransactionRepository()
        self._seed(repo)

        rows = repo.get_transactions(sort_by="date", sort_order="asc")

        assert [t["transactionId"] for t in rows] == [
            "tx-old-small",
            "tx-mid-large",
            "tx-new-medium",
        ]

    def test_sorts_by_amount(self, mock_db_path):
        """Amounts are signed, so descending puts the smallest expense first."""
        repo = TransactionRepository()
        self._seed(repo)

        descending = repo.get_transactions(sort_by="amount", sort_order="desc")
        ascending = repo.get_transactions(sort_by="amount", sort_order="asc")

        assert [t["transactionValue"] for t in descending] == [-5.0, -50.0, -100.0]
        assert [t["transactionValue"] for t in ascending] == [-100.0, -50.0, -5.0]

    def test_sorts_by_description(self, mock_db_path):
        repo = TransactionRepository()
        self._seed(repo)

        rows = repo.get_transactions(sort_by="description", sort_order="asc")

        assert [t["description"] for t in rows] == ["Almonds", "Beans", "Cutlery"]

    def test_unknown_sort_field_falls_back_to_the_default(self, mock_db_path):
        """An unrecognised column must never reach the SQL — the route
        rejects one first, but the repository is not allowed to interpolate
        whatever it is handed."""
        repo = TransactionRepository()
        self._seed(repo)

        rows = repo.get_transactions(sort_by="t.transactionValue; DROP TABLE")

        assert [t["transactionId"] for t in rows] == [
            "tx-new-medium",
            "tx-mid-large",
            "tx-old-small",
        ]

    def test_paging_is_stable_when_the_sort_key_ties(self, mock_db_path):
        """Every sort key has ties. Without a deterministic tiebreaker the
        order of tied rows is left to the query plan, and a row can repeat on
        one page while another is skipped."""
        repo = TransactionRepository()
        repo.persist(
            "IBAN1",
            [
                _make_transaction(
                    transactionId=f"tx-{index}",
                    transactionDate="2026-07-01T00:00:00",
                    transactionValue=-10.0,
                )
                for index in range(6)
            ],
        )

        first = repo.get_transactions(limit=3, offset=0)
        second = repo.get_transactions(limit=3, offset=3)
        seen = [t["transactionId"] for t in first + second]

        # Every row appears exactly once across the two pages, in the order
        # the tiebreaker fixes rather than whatever the plan happens to emit.
        assert seen == ["tx-5", "tx-4", "tx-3", "tx-2", "tx-1", "tx-0"]
        assert repo.get_count() == 6

    def test_ties_break_with_the_sort_direction(self, mock_db_path):
        repo = TransactionRepository()
        repo.persist(
            "IBAN1",
            [
                _make_transaction(
                    transactionId=f"tx-{index}",
                    transactionDate="2026-07-01T00:00:00",
                )
                for index in range(3)
            ],
        )

        rows = repo.get_transactions(sort_order="asc")

        assert [t["transactionId"] for t in rows] == ["tx-0", "tx-1", "tx-2"]


@pytest.mark.unit
class TestTransactionRepositoryMagnitudeFilter:
    """Test the sign-insensitive amount filter."""

    @staticmethod
    def _seed(repo: TransactionRepository) -> None:
        repo.persist(
            "IBAN1",
            [
                _make_transaction(transactionId="tx-expense", transactionValue=-45.30),
                _make_transaction(transactionId="tx-income", transactionValue=45.00),
                _make_transaction(transactionId="tx-small", transactionValue=-5.00),
                _make_transaction(transactionId="tx-large", transactionValue=-500.00),
            ],
        )

    def test_matches_income_and_expenses_of_the_same_size(self, mock_db_path):
        repo = TransactionRepository()
        self._seed(repo)

        rows = repo.get_transactions(min_magnitude=40, max_magnitude=50)

        assert sorted(t["transactionId"] for t in rows) == ["tx-expense", "tx-income"]

    def test_count_respects_the_magnitude_filter(self, mock_db_path):
        repo = TransactionRepository()
        self._seed(repo)

        assert repo.get_count(min_magnitude=40, max_magnitude=50) == 2
        assert repo.get_count(min_magnitude=100) == 1
        assert repo.get_count(max_magnitude=10) == 1

    def test_zero_lower_bound_is_not_treated_as_absent(self, mock_db_path):
        """0 is falsy; the clause has to test for None, not truthiness."""
        repo = TransactionRepository()
        self._seed(repo)

        assert repo.get_count(min_magnitude=0, max_magnitude=10) == 1
