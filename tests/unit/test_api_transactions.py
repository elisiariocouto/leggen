"""Tests for transactions API endpoints."""

import pytest
from unittest.mock import patch
from datetime import datetime


@pytest.mark.api
class TestTransactionsAPI:
    """Test transaction-related API endpoints."""

    def test_get_all_transactions_success(
        self, api_client, mock_config, mock_auth_token
    ):
        """Test successful retrieval of all transactions from database."""
        mock_transactions = [
            {
                "internalTransactionId": "txn-001",
                "institutionId": "REVOLUT_REVOLT21",
                "iban": "LT313250081177977789",
                "transactionDate": datetime(2025, 9, 1, 9, 30),
                "description": "Coffee Shop Payment",
                "transactionValue": -10.50,
                "transactionCurrency": "EUR",
                "transactionStatus": "booked",
                "accountId": "test-account-123",
                "rawTransaction": {"some": "data"},
            },
            {
                "internalTransactionId": "txn-002",
                "institutionId": "REVOLUT_REVOLT21",
                "iban": "LT313250081177977789",
                "transactionDate": datetime(2025, 9, 2, 14, 15),
                "description": "Grocery Store",
                "transactionValue": -45.30,
                "transactionCurrency": "EUR",
                "transactionStatus": "booked",
                "accountId": "test-account-123",
                "rawTransaction": {"other": "data"},
            },
        ]

        with (
            patch("leggend.config.config", mock_config),
            patch(
                "leggend.api.routes.transactions.database_service.get_transactions_from_db",
                return_value=mock_transactions,
            ),
            patch(
                "leggend.api.routes.transactions.database_service.get_transaction_count_from_db",
                return_value=2,
            ),
        ):
            response = api_client.get("/api/v1/transactions?summary_only=true")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
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
        self, api_client, mock_config, mock_auth_token
    ):
        """Test retrieval of full transaction details from database."""
        mock_transactions = [
            {
                "internalTransactionId": "txn-001",
                "institutionId": "REVOLUT_REVOLT21",
                "iban": "LT313250081177977789",
                "transactionDate": datetime(2025, 9, 1, 9, 30),
                "description": "Coffee Shop Payment",
                "transactionValue": -10.50,
                "transactionCurrency": "EUR",
                "transactionStatus": "booked",
                "accountId": "test-account-123",
                "rawTransaction": {"some": "raw_data"},
            }
        ]

        with (
            patch("leggend.config.config", mock_config),
            patch(
                "leggend.api.routes.transactions.database_service.get_transactions_from_db",
                return_value=mock_transactions,
            ),
            patch(
                "leggend.api.routes.transactions.database_service.get_transaction_count_from_db",
                return_value=1,
            ),
        ):
            response = api_client.get("/api/v1/transactions?summary_only=false")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1

        transaction = data["data"][0]
        assert transaction["internal_transaction_id"] == "txn-001"
        assert transaction["institution_id"] == "REVOLUT_REVOLT21"
        assert transaction["iban"] == "LT313250081177977789"
        assert "raw_transaction" in transaction

    def test_get_transactions_with_filters(
        self, api_client, mock_config, mock_auth_token
    ):
        """Test getting transactions with various filters."""
        mock_transactions = [
            {
                "internalTransactionId": "txn-001",
                "institutionId": "REVOLUT_REVOLT21",
                "iban": "LT313250081177977789",
                "transactionDate": datetime(2025, 9, 1, 9, 30),
                "description": "Coffee Shop Payment",
                "transactionValue": -10.50,
                "transactionCurrency": "EUR",
                "transactionStatus": "booked",
                "accountId": "test-account-123",
                "rawTransaction": {"some": "data"},
            }
        ]

        with (
            patch("leggend.config.config", mock_config),
            patch(
                "leggend.api.routes.transactions.database_service.get_transactions_from_db",
                return_value=mock_transactions,
            ) as mock_get_transactions,
            patch(
                "leggend.api.routes.transactions.database_service.get_transaction_count_from_db",
                return_value=1,
            ),
        ):
            response = api_client.get(
                "/api/v1/transactions?"
                "account_id=test-account-123&"
                "date_from=2025-09-01&"
                "date_to=2025-09-02&"
                "min_amount=-50.0&"
                "max_amount=0.0&"
                "search=Coffee&"
                "limit=10&"
                "offset=5"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify the database service was called with correct filters
        mock_get_transactions.assert_called_once_with(
            account_id="test-account-123",
            limit=10,
            offset=5,
            date_from="2025-09-01",
            date_to="2025-09-02",
            min_amount=-50.0,
            max_amount=0.0,
            search="Coffee",
            hide_missing_ids=True,
        )

    def test_get_transactions_empty_result(
        self, api_client, mock_config, mock_auth_token
    ):
        """Test getting transactions when database returns empty result."""
        with (
            patch("leggend.config.config", mock_config),
            patch(
                "leggend.api.routes.transactions.database_service.get_transactions_from_db",
                return_value=[],
            ),
            patch(
                "leggend.api.routes.transactions.database_service.get_transaction_count_from_db",
                return_value=0,
            ),
        ):
            response = api_client.get("/api/v1/transactions")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 0
        assert "0 transactions" in data["message"]

    def test_get_transactions_database_error(
        self, api_client, mock_config, mock_auth_token
    ):
        """Test handling database error when getting transactions."""
        with (
            patch("leggend.config.config", mock_config),
            patch(
                "leggend.api.routes.transactions.database_service.get_transactions_from_db",
                side_effect=Exception("Database connection failed"),
            ),
        ):
            response = api_client.get("/api/v1/transactions")

        assert response.status_code == 500
        assert "Failed to get transactions" in response.json()["detail"]

    def test_get_transaction_stats_success(
        self, api_client, mock_config, mock_auth_token
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

        with (
            patch("leggend.config.config", mock_config),
            patch(
                "leggend.api.routes.transactions.database_service.get_transactions_from_db",
                return_value=mock_transactions,
            ),
        ):
            response = api_client.get("/api/v1/transactions/stats?days=30")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        stats = data["data"]
        assert stats["period_days"] == 30
        assert stats["total_transactions"] == 3
        assert stats["booked_transactions"] == 2
        assert stats["pending_transactions"] == 1
        assert stats["total_income"] == 100.00
        assert stats["total_expenses"] == 35.80  # abs(-10.50) + abs(-25.30)
        assert stats["net_change"] == 64.20  # 100.00 - 35.80
        assert stats["accounts_included"] == 2  # Two unique account IDs

        # Average transaction: ((-10.50) + 100.00 + (-25.30)) / 3 = 64.20 / 3 = 21.4
        expected_avg = round(64.20 / 3, 2)
        assert stats["average_transaction"] == expected_avg

    def test_get_transaction_stats_with_account_filter(
        self, api_client, mock_config, mock_auth_token
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

        with (
            patch("leggend.config.config", mock_config),
            patch(
                "leggend.api.routes.transactions.database_service.get_transactions_from_db",
                return_value=mock_transactions,
            ) as mock_get_transactions,
        ):
            response = api_client.get(
                "/api/v1/transactions/stats?account_id=test-account-123"
            )

        assert response.status_code == 200

        # Verify the database service was called with account filter
        mock_get_transactions.assert_called_once()
        call_kwargs = mock_get_transactions.call_args.kwargs
        assert call_kwargs["account_id"] == "test-account-123"

    def test_get_transaction_stats_empty_result(
        self, api_client, mock_config, mock_auth_token
    ):
        """Test getting stats when no transactions match criteria."""
        with (
            patch("leggend.config.config", mock_config),
            patch(
                "leggend.api.routes.transactions.database_service.get_transactions_from_db",
                return_value=[],
            ),
        ):
            response = api_client.get("/api/v1/transactions/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        stats = data["data"]
        assert stats["total_transactions"] == 0
        assert stats["total_income"] == 0.0
        assert stats["total_expenses"] == 0.0
        assert stats["net_change"] == 0.0
        assert stats["average_transaction"] == 0  # Division by zero handled
        assert stats["accounts_included"] == 0

    def test_get_transaction_stats_database_error(
        self, api_client, mock_config, mock_auth_token
    ):
        """Test handling database error when getting stats."""
        with (
            patch("leggend.config.config", mock_config),
            patch(
                "leggend.api.routes.transactions.database_service.get_transactions_from_db",
                side_effect=Exception("Database connection failed"),
            ),
        ):
            response = api_client.get("/api/v1/transactions/stats")

        assert response.status_code == 500
        assert "Failed to get transaction stats" in response.json()["detail"]

    def test_get_transaction_stats_custom_period(
        self, api_client, mock_config, mock_auth_token
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

        with (
            patch("leggend.config.config", mock_config),
            patch(
                "leggend.api.routes.transactions.database_service.get_transactions_from_db",
                return_value=mock_transactions,
            ) as mock_get_transactions,
        ):
            response = api_client.get("/api/v1/transactions/stats?days=7")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["period_days"] == 7

        # Verify the date range was calculated correctly for 7 days
        mock_get_transactions.assert_called_once()
        call_kwargs = mock_get_transactions.call_args.kwargs
        assert "date_from" in call_kwargs
        assert "date_to" in call_kwargs
