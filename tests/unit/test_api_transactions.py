"""Tests for transactions API endpoints."""

from datetime import datetime
from unittest.mock import patch

import pytest

from leggen.repositories import TransactionRepository
from tests.conftest import persist_transactions


@pytest.mark.api
class TestTransactionsAPI:
    """Test transaction-related API endpoints."""

    def test_get_all_transactions_success(
        self,
        fastapi_app,
        api_client,
        mock_config,
        mock_transaction_repo,
    ):
        """Test successful retrieval of all transactions from database."""
        mock_transactions = [
            {
                "transactionId": "bank-txn-001",  # NEW: stable bank-provided ID
                "internalTransactionId": "txn-001",
                "institutionId": "REVOLUT_REVOLT21",
                "iban": "LT313250081177977789",
                "transactionDate": datetime(2025, 9, 1, 9, 30),
                "description": "Coffee Shop Payment",
                "transactionValue": -10.50,
                "transactionCurrency": "EUR",
                "transactionStatus": "booked",
                "accountId": "test-account-123",
                "rawTransaction": {"transactionId": "bank-txn-001", "some": "data"},
            },
            {
                "transactionId": "bank-txn-002",  # NEW: stable bank-provided ID
                "internalTransactionId": "txn-002",
                "institutionId": "REVOLUT_REVOLT21",
                "iban": "LT313250081177977789",
                "transactionDate": datetime(2025, 9, 2, 14, 15),
                "description": "Grocery Store",
                "transactionValue": -45.30,
                "transactionCurrency": "EUR",
                "transactionStatus": "booked",
                "accountId": "test-account-123",
                "rawTransaction": {"transactionId": "bank-txn-002", "other": "data"},
            },
        ]

        mock_transaction_repo.get_transactions.return_value = mock_transactions
        mock_transaction_repo.get_count.return_value = len(mock_transactions)
        fastapi_app.dependency_overrides[TransactionRepository] = lambda: (
            mock_transaction_repo
        )

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get("/api/v1/transactions?summary_only=true")

        fastapi_app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2

        # Check first transaction summary
        transaction = data["data"][0]
        assert transaction["internal_transaction_id"] == "txn-001"
        assert transaction["amount"] == -10.50
        assert transaction["currency"] == "EUR"
        assert transaction["description"] == "Coffee Shop Payment"
        assert transaction["status"] == "booked"
        assert transaction["account_id"] == "test-account-123"

    def test_get_all_transactions_full_details(
        self,
        fastapi_app,
        api_client,
        mock_config,
        mock_transaction_repo,
    ):
        """Test retrieval of full transaction details from database."""
        mock_transactions = [
            {
                "transactionId": "bank-txn-001",  # NEW: stable bank-provided ID
                "internalTransactionId": "txn-001",
                "institutionId": "REVOLUT_REVOLT21",
                "iban": "LT313250081177977789",
                "transactionDate": datetime(2025, 9, 1, 9, 30),
                "description": "Coffee Shop Payment",
                "transactionValue": -10.50,
                "transactionCurrency": "EUR",
                "transactionStatus": "booked",
                "accountId": "test-account-123",
                "rawTransaction": {"transactionId": "bank-txn-001", "some": "raw_data"},
            }
        ]

        mock_transaction_repo.get_transactions.return_value = mock_transactions
        mock_transaction_repo.get_count.return_value = len(mock_transactions)
        fastapi_app.dependency_overrides[TransactionRepository] = lambda: (
            mock_transaction_repo
        )

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get("/api/v1/transactions?summary_only=false")

        fastapi_app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1

        transaction = data["data"][0]
        assert transaction["transaction_id"] == "bank-txn-001"  # NEW: check stable ID
        assert transaction["internal_transaction_id"] == "txn-001"
        assert transaction["institution_id"] == "REVOLUT_REVOLT21"
        assert transaction["iban"] == "LT313250081177977789"
        assert "raw_transaction" in transaction

    def test_get_transactions_with_filters(
        self,
        fastapi_app,
        api_client,
        mock_config,
        mock_transaction_repo,
    ):
        """Test getting transactions with various filters."""
        mock_transactions = [
            {
                "transactionId": "bank-txn-001",  # NEW: stable bank-provided ID
                "internalTransactionId": "txn-001",
                "institutionId": "REVOLUT_REVOLT21",
                "iban": "LT313250081177977789",
                "transactionDate": datetime(2025, 9, 1, 9, 30),
                "description": "Coffee Shop Payment",
                "transactionValue": -10.50,
                "transactionCurrency": "EUR",
                "transactionStatus": "booked",
                "accountId": "test-account-123",
                "rawTransaction": {"transactionId": "bank-txn-001", "some": "data"},
            }
        ]

        mock_transaction_repo.get_transactions.return_value = mock_transactions
        mock_transaction_repo.get_count.return_value = 1

        fastapi_app.dependency_overrides[TransactionRepository] = lambda: (
            mock_transaction_repo
        )

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get(
                "/api/v1/transactions?"
                "account_id=test-account-123&"
                "date_from=2025-09-01&"
                "date_to=2025-09-02&"
                "min_amount=-50.0&"
                "max_amount=0.0&"
                "search=Coffee&"
                "page=2&"
                "per_page=10"
            )

        fastapi_app.dependency_overrides.clear()

        assert response.status_code == 200

        # Verify the repository was called with correct filters
        mock_transaction_repo.get_transactions.assert_called_once_with(
            account_id="test-account-123",
            limit=10,
            offset=10,  # (page-1) * per_page = (2-1) * 10 = 10
            date_from="2025-09-01",
            date_to="2025-09-02",
            min_amount=-50.0,
            max_amount=0.0,
            search="Coffee",
            category_id=None,
        )

    def test_get_transactions_empty_result(
        self,
        fastapi_app,
        api_client,
        mock_config,
        mock_transaction_repo,
    ):
        """Test getting transactions when database returns empty result."""
        mock_transaction_repo.get_transactions.return_value = []
        mock_transaction_repo.get_count.return_value = 0

        fastapi_app.dependency_overrides[TransactionRepository] = lambda: (
            mock_transaction_repo
        )

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get("/api/v1/transactions")

        fastapi_app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 0
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["total_pages"] == 0

    def test_get_transactions_database_error(
        self,
        fastapi_app,
        raw_api_client,
        mock_transaction_repo,
    ):
        """A repository error surfaces as the sanitized global 500."""
        mock_transaction_repo.get_transactions.side_effect = Exception(
            "Database connection failed"
        )

        fastapi_app.dependency_overrides[TransactionRepository] = lambda: (
            mock_transaction_repo
        )

        response = raw_api_client.get("/api/v1/transactions")

        fastapi_app.dependency_overrides.clear()

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
        assert data["average_transaction"] == round(64.20 / 3, 2)

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
        category_repo.assign_category(
            account_id="acc-1",
            transaction_id="t2",
            category_id=cat["id"],
            description="Transaction t2",
            creditor_name="",
            debtor_name="",
        )

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
        assert data["average_transaction"] == 20.00  # (50 - 10) / 2 EUR txns

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

    def test_get_transaction_stats_database_error(
        self,
        fastapi_app,
        raw_api_client,
        mock_transaction_repo,
    ):
        """A repository error surfaces as the sanitized global 500."""
        mock_transaction_repo.get_stats_totals.side_effect = Exception(
            "Database connection failed"
        )

        fastapi_app.dependency_overrides[TransactionRepository] = lambda: (
            mock_transaction_repo
        )

        response = raw_api_client.get(
            "/api/v1/transactions/stats?date_from=2025-01-01&date_to=2025-12-31"
        )

        fastapi_app.dependency_overrides.clear()

        assert response.status_code == 500
        assert response.json()["detail"] == "Internal server error."

    def test_get_transactions_invalid_per_page(self, api_client, mock_config):
        """per_page below 1 is rejected instead of dividing by zero."""
        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get("/api/v1/transactions?per_page=0")
        assert response.status_code == 422

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get("/api/v1/transactions?per_page=-5")
        assert response.status_code == 422

    def test_get_transactions_invalid_category_id(self, api_client, mock_config):
        """Non-numeric category_id is rejected with 422, not a 500."""
        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get("/api/v1/transactions?category_id=abc")
        assert response.status_code == 422

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get(
                "/api/v1/transactions/stats"
                "?date_from=2025-01-01&date_to=2025-01-31&category_id=abc"
            )
        assert response.status_code == 422
