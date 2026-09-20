"""Tests for transactions API endpoints."""

from unittest.mock import MagicMock

import pytest

from leggen.repositories import TransactionRepository
from tests.helpers import DEFAULT_IBAN, persist_transactions, seed_transactions


@pytest.mark.api
class TestTransactionsAPI:
    """Test transaction-related API endpoints."""

    def test_get_all_transactions_summary(self, api_client):
        """The default listing is newest-first summaries."""
        seed_transactions(
            [
                {
                    "id": "bank-txn-001",
                    "account_id": "test-account-123",
                    "date": "2025-09-01T09:30:00",
                    "description": "Coffee Shop Payment",
                    "value": -10.50,
                },
                {
                    "id": "bank-txn-002",
                    "account_id": "test-account-123",
                    "date": "2025-09-02T14:15:00",
                    "description": "Grocery Store",
                    "value": -45.30,
                },
            ]
        )

        response = api_client.get("/api/v1/transactions?summary_only=true")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert [t["transaction_id"] for t in data["data"]] == [
            "bank-txn-002",
            "bank-txn-001",
        ]

        transaction = data["data"][1]
        assert transaction["internal_transaction_id"] == "int-bank-txn-001"
        assert transaction["amount"] == -10.50
        assert transaction["currency"] == "EUR"
        assert transaction["description"] == "Coffee Shop Payment"
        assert transaction["status"] == "booked"
        assert transaction["account_id"] == "test-account-123"
        assert "raw_transaction" not in transaction

    def test_get_all_transactions_full_details(self, api_client):
        """summary_only=false returns the stored row including the raw payload."""
        raw = {"transactionId": "bank-txn-001", "some": "raw_data"}
        seed_transactions(
            [
                {
                    "id": "bank-txn-001",
                    "account_id": "test-account-123",
                    "date": "2025-09-01T09:30:00",
                    "description": "Coffee Shop Payment",
                    "value": -10.50,
                    "raw": raw,
                }
            ]
        )

        response = api_client.get("/api/v1/transactions?summary_only=false")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1

        transaction = data["data"][0]
        assert transaction["transaction_id"] == "bank-txn-001"
        assert transaction["internal_transaction_id"] == "int-bank-txn-001"
        assert transaction["institution_id"] == "TEST_BANK"
        assert transaction["iban"] == DEFAULT_IBAN
        assert transaction["raw_transaction"] == raw

    def test_get_transactions_with_filters(self, api_client):
        """Account, date range, amount range and search combine."""
        seed_transactions(
            [
                {
                    "id": "coffee",
                    "account_id": "test-account-123",
                    "date": "2025-09-01T09:30:00",
                    "description": "Coffee Shop Payment",
                    "value": -10.50,
                },
                {
                    "id": "grocery",
                    "account_id": "test-account-123",
                    "date": "2025-09-01T14:15:00",
                    "description": "Grocery Store",
                    "value": -45.30,
                },
                {
                    "id": "late-coffee",
                    "account_id": "test-account-123",
                    "date": "2025-09-10T08:00:00",
                    "description": "Coffee Shop Payment",
                    "value": -3.0,
                },
                {
                    "id": "big-coffee",
                    "account_id": "test-account-123",
                    "date": "2025-09-01T12:00:00",
                    "description": "Coffee Beans",
                    "value": -60.0,
                },
                {
                    "id": "other-account",
                    "account_id": "other",
                    "date": "2025-09-01T12:00:00",
                    "description": "Coffee Shop Payment",
                    "value": -8.0,
                },
            ]
        )

        response = api_client.get(
            "/api/v1/transactions?"
            "account_id=test-account-123&"
            "date_from=2025-09-01&"
            "date_to=2025-09-02&"
            "min_amount=-50.0&"
            "max_amount=0.0&"
            "search=Coffee"
        )

        assert response.status_code == 200
        data = response.json()
        assert [t["transaction_id"] for t in data["data"]] == ["coffee"]
        assert data["total"] == 1

    def test_get_transactions_pagination(self, api_client):
        """The total counts every match; pages report their neighbours."""
        persist_transactions(
            [
                (f"txn-{i}", "acc-1", f"2025-09-0{i}T10:00:00", -1.0, "EUR", "booked")
                for i in range(1, 4)
            ]
        )

        first = api_client.get("/api/v1/transactions?per_page=2&page=1").json()
        second = api_client.get("/api/v1/transactions?per_page=2&page=2").json()

        assert [t["transaction_id"] for t in first["data"]] == ["txn-3", "txn-2"]
        assert first["total"] == 3
        assert first["total_pages"] == 2
        assert first["has_next"] is True
        assert first["has_prev"] is False
        assert [t["transaction_id"] for t in second["data"]] == ["txn-1"]
        assert second["has_next"] is False
        assert second["has_prev"] is True

    def test_get_transactions_empty_result(self, api_client):
        response = api_client.get("/api/v1/transactions")

        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["total_pages"] == 0

    def test_get_transactions_database_error(self, raw_api_client, override):
        """A repository error surfaces as the sanitized global 500."""
        repo = MagicMock()
        repo.get_transactions.side_effect = Exception("Database connection failed")
        override(TransactionRepository, repo)

        response = raw_api_client.get("/api/v1/transactions")

        assert response.status_code == 500
        assert response.json()["detail"] == "Internal server error."

    @staticmethod
    def _persist_txns(rows: list[tuple]) -> None:
        persist_transactions(rows)

    def test_get_transaction_stats_success(self, api_client, mock_db_path):
        """Stats are aggregated in SQL over the real database."""
        self._persist_txns(
            [
                ("t1", "acc-1", "2025-09-01T09:30:00", -10.50, "EUR", "booked"),
                ("t2", "acc-1", "2025-09-02T14:15:00", 100.00, "EUR", "pending"),
                ("t3", "acc-2", "2025-09-03T16:45:00", -25.30, "EUR", "booked"),
            ]
        )

        response = api_client.get(
            "/api/v1/transactions/stats?date_from=2025-08-01&date_to=2025-10-01"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["date_from"] == "2025-08-01"
        assert data["date_to"] == "2025-10-01"
        assert data["total_transactions"] == 3
        assert data["booked_transactions"] == 2
        assert data["pending_transactions"] == 1
        assert data["currency"] == "EUR"
        assert data["total_income"] == 100.00
        assert data["total_expenses"] == 35.80  # abs(-10.50) + abs(-25.30)
        assert data["net_change"] == 64.20  # 100.00 - 35.80
        assert data["accounts_included"] == 2  # Two unique account IDs
        # Mean transaction *size*, not net/count: (100.00 + 10.50 + 25.30) / 3
        assert data["average_transaction"] == round(135.80 / 3, 2)

    def test_get_transaction_stats_with_account_filter(self, api_client, mock_db_path):
        """Stats filtered by account only aggregate that account."""
        self._persist_txns(
            [
                ("t1", "acc-1", "2025-09-01T09:30:00", -10.50, "EUR", "booked"),
                ("t2", "acc-2", "2025-09-02T14:15:00", 100.00, "EUR", "booked"),
            ]
        )

        response = api_client.get(
            "/api/v1/transactions/stats"
            "?date_from=2025-08-01&date_to=2025-10-01&account_id=acc-1"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_transactions"] == 1
        assert data["total_expenses"] == 10.50
        assert data["total_income"] == 0
        assert data["accounts_included"] == 1

    def test_get_transaction_stats_respects_date_range(self, api_client, mock_db_path):
        """Transactions outside the requested range are not aggregated,
        and the inclusive end date covers the whole day."""
        self._persist_txns(
            [
                ("t1", "acc-1", "2025-08-27T09:30:00", -10.00, "EUR", "booked"),
                ("t2", "acc-1", "2025-09-01T14:15:00", -20.00, "EUR", "booked"),
                ("t3", "acc-1", "2025-09-04T23:00:00", -40.00, "EUR", "booked"),
                ("t4", "acc-1", "2025-09-05T00:30:00", -80.00, "EUR", "booked"),
            ]
        )

        response = api_client.get(
            "/api/v1/transactions/stats?date_from=2025-08-28&date_to=2025-09-04"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_transactions"] == 2
        assert data["total_expenses"] == 60.00  # t2 + t3; t1/t4 out of range

    def test_get_transaction_stats_excludes_flagged_categories(
        self, api_client, mock_db_path
    ):
        """Transactions in categories flagged exclude_from_stats are left out."""
        from leggen.repositories.category_repository import CategoryRepository

        self._persist_txns(
            [
                ("t1", "acc-1", "2025-09-01T09:30:00", -10.00, "EUR", "booked"),
                ("t2", "acc-1", "2025-09-02T14:15:00", -20.00, "EUR", "booked"),
            ]
        )
        category_repo = CategoryRepository()
        cat = category_repo.create_category(
            name="Internal transfers", color="#000000", exclude_from_stats=True
        )
        category_repo.assign_category("acc-1", "t2", cat["id"])

        response = api_client.get(
            "/api/v1/transactions/stats?date_from=2025-08-01&date_to=2025-10-01"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_transactions"] == 1
        assert data["total_expenses"] == 10.00

    def test_get_transaction_stats_uses_dominant_currency(
        self, api_client, mock_db_path
    ):
        """Money totals cover only the dominant currency; counts cover all."""
        self._persist_txns(
            [
                ("t1", "acc-1", "2025-09-01T09:30:00", -10.00, "EUR", "booked"),
                ("t2", "acc-1", "2025-09-02T14:15:00", 50.00, "EUR", "booked"),
                ("t3", "acc-1", "2025-09-03T16:45:00", -999.00, "USD", "booked"),
            ]
        )

        response = api_client.get(
            "/api/v1/transactions/stats?date_from=2025-08-01&date_to=2025-10-01"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_transactions"] == 3
        assert data["currency"] == "EUR"
        assert data["total_expenses"] == 10.00  # USD amount not mixed in
        assert data["total_income"] == 50.00
        assert data["average_transaction"] == 30.00  # (50 + 10) / 2 EUR txns

    def test_get_transaction_stats_empty_result(self, api_client, mock_db_path):
        """Stats over an empty database return zeroed totals."""
        response = api_client.get(
            "/api/v1/transactions/stats?date_from=2025-01-01&date_to=2025-12-31"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total_transactions"] == 0
        assert data["total_income"] == 0.0
        assert data["total_expenses"] == 0.0
        assert data["net_change"] == 0.0
        assert data["average_transaction"] == 0  # Division by zero handled
        assert data["accounts_included"] == 0
        assert data["currency"] is None

    def test_get_transaction_stats_database_error(self, raw_api_client, override):
        """A repository error surfaces as the sanitized global 500."""
        repo = MagicMock()
        repo.get_stats_totals.side_effect = Exception("Database connection failed")
        override(TransactionRepository, repo)

        response = raw_api_client.get(
            "/api/v1/transactions/stats?date_from=2025-01-01&date_to=2025-12-31"
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "Internal server error."

    def test_get_transactions_invalid_per_page(self, api_client):
        """per_page below 1 is rejected instead of dividing by zero."""
        response = api_client.get("/api/v1/transactions?per_page=0")
        assert response.status_code == 422

        response = api_client.get("/api/v1/transactions?per_page=-5")
        assert response.status_code == 422

    def test_get_transactions_filtered_by_status(self, api_client, mock_db_path):
        """Only transactions in the requested status come back, and the
        pagination total counts the filtered set."""
        persist_transactions(
            [
                ("t1", "acc-1", "2025-09-01T09:30:00", -10.50, "EUR", "booked"),
                ("t2", "acc-1", "2025-09-02T14:15:00", -20.00, "EUR", "pending"),
                ("t3", "acc-1", "2025-09-03T16:45:00", -30.00, "EUR", "booked"),
            ]
        )

        response = api_client.get("/api/v1/transactions?status=pending")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert [txn["transaction_id"] for txn in data["data"]] == ["t2"]
        assert data["data"][0]["status"] == "pending"

    def test_get_transactions_without_status_filter_returns_all(
        self, api_client, mock_db_path
    ):
        """Omitting the status filter leaves both statuses in the result."""
        persist_transactions(
            [
                ("t1", "acc-1", "2025-09-01T09:30:00", -10.50, "EUR", "booked"),
                ("t2", "acc-1", "2025-09-02T14:15:00", -20.00, "EUR", "pending"),
            ]
        )

        response = api_client.get("/api/v1/transactions")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_get_transactions_invalid_status(self, api_client):
        """An unknown status is rejected with 422 rather than silently
        returning an empty page."""
        response = api_client.get("/api/v1/transactions?status=nonsense")
        assert response.status_code == 422

    def test_get_transactions_invalid_sort_params(self, api_client):
        """Sort params are constrained to the allowlist, so an unknown column
        is a 422 and never reaches the ORDER BY."""
        response = api_client.get("/api/v1/transactions?sort_by=transactionValue")
        assert response.status_code == 422

        response = api_client.get("/api/v1/transactions?sort_order=sideways")
        assert response.status_code == 422

    def test_get_transactions_negative_magnitude_rejected(self, api_client):
        """Magnitudes are sizes, so a negative bound is meaningless."""
        response = api_client.get("/api/v1/transactions?min_magnitude=-5")
        assert response.status_code == 422

    def test_get_transactions_sorted_by_amount(self, api_client, mock_db_path):
        """Sorting runs in SQL over the whole result set, not just a page."""
        self._persist_txns(
            [
                ("t1", "acc-1", "2025-09-01T10:00:00", -5.0, "EUR", "booked"),
                ("t2", "acc-1", "2025-09-02T10:00:00", -500.0, "EUR", "booked"),
                ("t3", "acc-1", "2025-09-03T10:00:00", -50.0, "EUR", "booked"),
            ]
        )

        response = api_client.get(
            "/api/v1/transactions?sort_by=amount&sort_order=asc&summary_only=false"
        )

        assert response.status_code == 200
        data = response.json()
        assert [txn["transaction_id"] for txn in data["data"]] == ["t2", "t3", "t1"]

    def test_get_transactions_magnitude_filter_matches_both_signs(
        self, api_client, mock_db_path
    ):
        """A magnitude range ignores the sign, so an expense and a refund of
        the same size both match — and the total agrees with the rows."""
        self._persist_txns(
            [
                ("t1", "acc-1", "2025-09-01T10:00:00", -45.30, "EUR", "booked"),
                ("t2", "acc-1", "2025-09-02T10:00:00", 45.00, "EUR", "booked"),
                ("t3", "acc-1", "2025-09-03T10:00:00", -500.0, "EUR", "booked"),
            ]
        )

        response = api_client.get(
            "/api/v1/transactions?min_magnitude=40&max_magnitude=50&summary_only=false"
        )

        assert response.status_code == 200
        data = response.json()
        assert sorted(txn["transaction_id"] for txn in data["data"]) == ["t1", "t2"]
        assert data["total"] == 2

    def test_get_transactions_kind_filter_splits_by_sign(
        self, api_client, mock_db_path
    ):
        """`kind` keeps one direction, so a list linked from an income or an
        expense figure holds exactly the rows that figure was summed from."""
        self._persist_txns(
            [
                ("t1", "acc-1", "2025-09-01T10:00:00", -45.30, "EUR", "booked"),
                ("t2", "acc-1", "2025-09-02T10:00:00", 1200.00, "EUR", "booked"),
                ("t3", "acc-1", "2025-09-03T10:00:00", -500.0, "EUR", "booked"),
            ]
        )

        response = api_client.get("/api/v1/transactions?kind=expense")
        assert response.status_code == 200
        data = response.json()
        assert sorted(txn["transaction_id"] for txn in data["data"]) == ["t1", "t3"]
        assert data["total"] == 2

        response = api_client.get("/api/v1/transactions?kind=income")
        assert response.status_code == 200
        data = response.json()
        assert [txn["transaction_id"] for txn in data["data"]] == ["t2"]
        assert data["total"] == 1

    def test_get_transactions_invalid_kind(self, api_client):
        """Anything but the two directions is a 422, not an unfiltered list."""
        response = api_client.get("/api/v1/transactions?kind=refund")
        assert response.status_code == 422

    def test_get_transactions_invalid_category_id(self, api_client):
        """Non-numeric category_id is rejected with 422, not a 500."""
        response = api_client.get("/api/v1/transactions?category_id=abc")
        assert response.status_code == 422

        response = api_client.get(
            "/api/v1/transactions/stats"
            "?date_from=2025-01-01&date_to=2025-01-31&category_id=abc"
        )
        assert response.status_code == 422


@pytest.mark.api
class TestUpdateTransaction:
    """PATCH /transactions/{account_id}/{transaction_id}"""

    def test_sets_and_clears_the_override(self, api_client, mock_db_path):
        persist_transactions(
            [("t1", "acc-1", "2025-09-05T10:00:00", -100.00, "EUR", "booked")]
        )

        response = api_client.patch(
            "/api/v1/transactions/acc-1/t1", json={"exclude_from_stats": True}
        )
        assert response.status_code == 200
        assert response.json()["exclude_from_stats"] is True
        assert response.json()["transaction_id"] == "t1"

        response = api_client.patch(
            "/api/v1/transactions/acc-1/t1", json={"exclude_from_stats": None}
        )
        assert response.status_code == 200
        assert response.json()["exclude_from_stats"] is None

    def test_override_is_visible_in_the_list(self, api_client, mock_db_path):
        persist_transactions(
            [("t1", "acc-1", "2025-09-05T10:00:00", -100.00, "EUR", "booked")]
        )
        api_client.patch(
            "/api/v1/transactions/acc-1/t1", json={"exclude_from_stats": False}
        )

        response = api_client.get("/api/v1/transactions")

        assert response.json()["data"][0]["exclude_from_stats"] is False

    def test_field_is_required(self, api_client, mock_db_path):
        """An empty body is a mistake, not a request to clear the override."""
        response = api_client.patch("/api/v1/transactions/acc-1/t1", json={})

        assert response.status_code == 422

    def test_unknown_transaction_is_404(self, api_client, mock_db_path):
        response = api_client.patch(
            "/api/v1/transactions/acc-1/nope", json={"exclude_from_stats": True}
        )

        assert response.status_code == 404
        assert response.json()["code"] == "NOT_FOUND"


@pytest.mark.api
class TestCategorySource:
    def test_reports_how_the_category_was_assigned(self, api_client, mock_db_path):
        from leggen.repositories import CategoryRepository, CategoryRuleRepository

        persist_transactions(
            [
                ("t1", "acc-1", "2025-09-05T10:00:00", -10.0, "EUR", "booked"),
                ("t2", "acc-1", "2025-09-06T10:00:00", -20.0, "EUR", "booked"),
                ("t3", "acc-1", "2025-09-07T10:00:00", -30.0, "EUR", "booked"),
            ]
        )
        groceries = next(
            c
            for c in CategoryRepository().get_all_categories()
            if c["name"] == "Groceries"
        )
        CategoryRepository().assign_category("acc-1", "t1", groceries["id"])
        rules = CategoryRuleRepository()
        rule = rules.create_rule("r", groceries["id"], "return true")
        rules.apply_assignments([("acc-1", "t2", groceries["id"], rule["id"], None)])

        rows = {
            t["transaction_id"]: t
            for t in api_client.get("/api/v1/transactions").json()["data"]
        }

        assert rows["t1"]["category_source"] == "manual"
        assert rows["t1"]["category_rule_id"] is None
        assert rows["t2"]["category_source"] == "rule"
        assert rows["t2"]["category_rule_id"] == rule["id"]
        assert rows["t3"]["category_source"] is None
