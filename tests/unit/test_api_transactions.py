"""Tests for transactions API endpoints."""

from datetime import datetime
from unittest.mock import patch

import pytest

from leggen.api.dependencies import get_transaction_repository


@pytest.mark.api
class TestTransactionsAPI:
    """Test transaction-related API endpoints."""

    def test_get_all_transactions_success(
        self,
        fastapi_app,
        api_client,
        mock_config,
        mock_auth_token,
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
        fastapi_app.dependency_overrides[get_transaction_repository] = (
            lambda: mock_transaction_repo
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
        mock_auth_token,
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
        fastapi_app.dependency_overrides[get_transaction_repository] = (
            lambda: mock_transaction_repo
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
        mock_auth_token,
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

        fastapi_app.dependency_overrides[get_transaction_repository] = (
            lambda: mock_transaction_repo
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
        )

    def test_get_transactions_empty_result(
        self,
        fastapi_app,
        api_client,
        mock_config,
        mock_auth_token,
        mock_transaction_repo,
    ):
        """Test getting transactions when database returns empty result."""
        mock_transaction_repo.get_transactions.return_value = []
        mock_transaction_repo.get_count.return_value = 0

        fastapi_app.dependency_overrides[get_transaction_repository] = (
            lambda: mock_transaction_repo
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
        api_client,
        mock_config,
        mock_auth_token,
        mock_transaction_repo,
    ):
        """Test handling database error when getting transactions."""
        mock_transaction_repo.get_transactions.side_effect = Exception(
            "Database connection failed"
        )

        fastapi_app.dependency_overrides[get_transaction_repository] = (
            lambda: mock_transaction_repo
        )

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get("/api/v1/transactions")

        fastapi_app.dependency_overrides.clear()

        assert response.status_code == 500
        assert "Failed to get transactions" in response.json()["detail"]

    def test_get_transaction_stats_success(
        self,
        fastapi_app,
        api_client,
        mock_config,
        mock_auth_token,
        mock_transaction_repo,
    ):
        """Test successful retrieval of transaction statistics from database."""
        mock_transactions = [
            {
                "internalTransactionId": "txn-001",
                "transactionDate": datetime(2025, 9, 1, 9, 30),
                "transactionValue": -10.50,
                "transactionStatus": "booked",
                "accountId": "test-account-123",
            },
            {
                "internalTransactionId": "txn-002",
                "transactionDate": datetime(2025, 9, 2, 14, 15),
                "transactionValue": 100.00,
                "transactionStatus": "pending",
                "accountId": "test-account-123",
            },
            {
                "internalTransactionId": "txn-003",
                "transactionDate": datetime(2025, 9, 3, 16, 45),
                "transactionValue": -25.30,
                "transactionStatus": "booked",
                "accountId": "other-account-456",
            },
        ]

        mock_transaction_repo.get_transactions.return_value = mock_transactions
        fastapi_app.dependency_overrides[get_transaction_repository] = (
            lambda: mock_transaction_repo
        )

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get("/api/v1/transactions/stats?days=30")

        fastapi_app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()

        assert data["period_days"] == 30
        assert data["total_transactions"] == 3
        assert data["booked_transactions"] == 2
        assert data["pending_transactions"] == 1
        assert data["total_income"] == 100.00
        assert data["total_expenses"] == 35.80  # abs(-10.50) + abs(-25.30)
        assert data["net_change"] == 64.20  # 100.00 - 35.80
        assert data["accounts_included"] == 2  # Two unique account IDs

        # Average transaction: ((-10.50) + 100.00 + (-25.30)) / 3 = 64.20 / 3 = 21.4
        expected_avg = round(64.20 / 3, 2)
        assert data["average_transaction"] == expected_avg

    def test_get_transaction_stats_with_account_filter(
        self,
        fastapi_app,
        api_client,
        mock_config,
        mock_auth_token,
        mock_transaction_repo,
    ):
        """Test getting transaction stats filtered by account."""
        mock_transactions = [
            {
                "internalTransactionId": "txn-001",
                "transactionDate": datetime(2025, 9, 1, 9, 30),
                "transactionValue": -10.50,
                "transactionStatus": "booked",
                "accountId": "test-account-123",
            }
        ]

        mock_transaction_repo.get_transactions.return_value = mock_transactions

        fastapi_app.dependency_overrides[get_transaction_repository] = (
            lambda: mock_transaction_repo
        )

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get(
                "/api/v1/transactions/stats?account_id=test-account-123"
            )

        fastapi_app.dependency_overrides.clear()

        assert response.status_code == 200

        # Verify the repository was called with account filter
        mock_transaction_repo.get_transactions.assert_called_once()
        call_kwargs = mock_transaction_repo.get_transactions.call_args.kwargs
        assert call_kwargs["account_id"] == "test-account-123"

    def test_get_transaction_stats_empty_result(
        self,
        fastapi_app,
        api_client,
        mock_config,
        mock_auth_token,
        mock_transaction_repo,
    ):
        """Test getting stats when no transactions match criteria."""
        mock_transaction_repo.get_transactions.return_value = []

        fastapi_app.dependency_overrides[get_transaction_repository] = (
            lambda: mock_transaction_repo
        )

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get("/api/v1/transactions/stats")

        fastapi_app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()

        assert data["total_transactions"] == 0
        assert data["total_income"] == 0.0
        assert data["total_expenses"] == 0.0
        assert data["net_change"] == 0.0
        assert data["average_transaction"] == 0  # Division by zero handled
        assert data["accounts_included"] == 0

    def test_get_transaction_stats_database_error(
        self,
        fastapi_app,
        api_client,
        mock_config,
        mock_auth_token,
        mock_transaction_repo,
    ):
        """Test handling database error when getting stats."""
        mock_transaction_repo.get_transactions.side_effect = Exception(
            "Database connection failed"
        )

        fastapi_app.dependency_overrides[get_transaction_repository] = (
            lambda: mock_transaction_repo
        )

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get("/api/v1/transactions/stats")

        fastapi_app.dependency_overrides.clear()

        assert response.status_code == 500
        assert "Failed to get transaction stats" in response.json()["detail"]

    def test_get_transaction_stats_custom_period(
        self,
        fastapi_app,
        api_client,
        mock_config,
        mock_auth_token,
        mock_transaction_repo,
    ):
        """Test getting transaction stats for custom time period."""
        mock_transactions = [
            {
                "internalTransactionId": "txn-001",
                "transactionDate": datetime(2025, 9, 1, 9, 30),
                "transactionValue": -10.50,
                "transactionStatus": "booked",
                "accountId": "test-account-123",
            }
        ]

        mock_transaction_repo.get_transactions.return_value = mock_transactions

        fastapi_app.dependency_overrides[get_transaction_repository] = (
            lambda: mock_transaction_repo
        )

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get("/api/v1/transactions/stats?days=7")

        fastapi_app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["period_days"] == 7

        # Verify the date range was calculated correctly for 7 days
        mock_transaction_repo.get_transactions.assert_called_once()
        call_kwargs = mock_transaction_repo.get_transactions.call_args.kwargs
        assert "date_from" in call_kwargs
        assert "date_to" in call_kwargs
