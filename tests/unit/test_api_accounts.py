"""Tests for accounts API endpoints."""

import pytest
from unittest.mock import patch


@pytest.mark.api
class TestAccountsAPI:
    """Test account-related API endpoints."""

    def test_get_all_accounts_success(
        self,
        api_client,
        mock_config,
        mock_auth_token,
        sample_account_data,
        mock_db_path,
    ):
        """Test successful retrieval of all accounts from database."""
        mock_accounts = [
            {
                "id": "test-account-123",
                "institution_id": "REVOLUT_REVOLT21",
                "status": "READY",
                "iban": "LT313250081177977789",
                "created": "2024-02-13T23:56:00Z",
                "last_accessed": "2025-09-01T09:30:00Z",
            }
        ]

        mock_balances = [
            {
                "id": 1,
                "account_id": "test-account-123",
                "bank": "REVOLUT_REVOLT21",
                "status": "active",
                "iban": "LT313250081177977789",
                "amount": 100.50,
                "currency": "EUR",
                "type": "interimAvailable",
                "timestamp": "2025-09-01T09:30:00Z",
            }
        ]

        with (
            patch("leggen.utils.config.config", mock_config),
            patch(
                "leggen.api.routes.accounts.database_service.get_accounts_from_db",
                return_value=mock_accounts,
            ),
            patch(
                "leggen.api.routes.accounts.database_service.get_balances_from_db",
                return_value=mock_balances,
            ),
        ):
            response = api_client.get("/api/v1/accounts")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        account = data["data"][0]
        assert account["id"] == "test-account-123"
        assert account["institution_id"] == "REVOLUT_REVOLT21"
        assert len(account["balances"]) == 1
        assert account["balances"][0]["amount"] == 100.50

    def test_get_account_details_success(
        self,
        api_client,
        mock_config,
        mock_auth_token,
        sample_account_data,
        mock_db_path,
    ):
        """Test successful retrieval of specific account details from database."""
        mock_account = {
            "id": "test-account-123",
            "institution_id": "REVOLUT_REVOLT21",
            "status": "READY",
            "iban": "LT313250081177977789",
            "created": "2024-02-13T23:56:00Z",
            "last_accessed": "2025-09-01T09:30:00Z",
        }

        mock_balances = [
            {
                "id": 1,
                "account_id": "test-account-123",
                "bank": "REVOLUT_REVOLT21",
                "status": "active",
                "iban": "LT313250081177977789",
                "amount": 250.75,
                "currency": "EUR",
                "type": "interimAvailable",
                "timestamp": "2025-09-01T09:30:00Z",
            }
        ]

        with (
            patch("leggen.utils.config.config", mock_config),
            patch(
                "leggen.api.routes.accounts.database_service.get_account_details_from_db",
                return_value=mock_account,
            ),
            patch(
                "leggen.api.routes.accounts.database_service.get_balances_from_db",
                return_value=mock_balances,
            ),
        ):
            response = api_client.get("/api/v1/accounts/test-account-123")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        account = data["data"]
        assert account["id"] == "test-account-123"
        assert account["iban"] == "LT313250081177977789"
        assert len(account["balances"]) == 1

    def test_get_account_balances_success(
        self, api_client, mock_config, mock_auth_token, mock_db_path
    ):
        """Test successful retrieval of account balances from database."""
        mock_balances = [
            {
                "id": 1,
                "account_id": "test-account-123",
                "bank": "REVOLUT_REVOLT21",
                "status": "active",
                "iban": "LT313250081177977789",
                "amount": 1000.00,
                "currency": "EUR",
                "type": "interimAvailable",
                "timestamp": "2025-09-01T10:00:00Z",
            },
            {
                "id": 2,
                "account_id": "test-account-123",
                "bank": "REVOLUT_REVOLT21",
                "status": "active",
                "iban": "LT313250081177977789",
                "amount": 950.00,
                "currency": "EUR",
                "type": "expected",
                "timestamp": "2025-09-01T10:00:00Z",
            },
        ]

        with (
            patch("leggen.utils.config.config", mock_config),
            patch(
                "leggen.api.routes.accounts.database_service.get_balances_from_db",
                return_value=mock_balances,
            ),
        ):
            response = api_client.get("/api/v1/accounts/test-account-123/balances")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2
        assert data["data"][0]["amount"] == 1000.00
        assert data["data"][0]["currency"] == "EUR"
        assert data["data"][0]["balance_type"] == "interimAvailable"

    def test_get_account_transactions_success(
        self,
        api_client,
        mock_config,
        mock_auth_token,
        sample_account_data,
        sample_transaction_data,
        mock_db_path,
    ):
        """Test successful retrieval of account transactions from database."""
        mock_transactions = [
            {
                "transactionId": "txn-bank-123",  # NEW: stable bank-provided ID
                "internalTransactionId": "txn-123",
                "institutionId": "REVOLUT_REVOLT21",
                "iban": "LT313250081177977789",
                "transactionDate": "2025-09-01T09:30:00Z",
                "description": "Coffee Shop Payment",
                "transactionValue": -10.50,
                "transactionCurrency": "EUR",
                "transactionStatus": "booked",
                "accountId": "test-account-123",
                "rawTransaction": {"transactionId": "txn-bank-123", "some": "data"},
            }
        ]

        with (
            patch("leggen.utils.config.config", mock_config),
            patch(
                "leggen.api.routes.accounts.database_service.get_transactions_from_db",
                return_value=mock_transactions,
            ),
            patch(
                "leggen.api.routes.accounts.database_service.get_transaction_count_from_db",
                return_value=1,
            ),
        ):
            response = api_client.get(
                "/api/v1/accounts/test-account-123/transactions?summary_only=true"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1

        transaction = data["data"][0]
        assert transaction["internal_transaction_id"] == "txn-123"
        assert transaction["amount"] == -10.50
        assert transaction["currency"] == "EUR"
        assert transaction["description"] == "Coffee Shop Payment"

    def test_get_account_transactions_full_details(
        self,
        api_client,
        mock_config,
        mock_auth_token,
        sample_account_data,
        sample_transaction_data,
        mock_db_path,
    ):
        """Test retrieval of full transaction details from database."""
        mock_transactions = [
            {
                "transactionId": "txn-bank-123",  # NEW: stable bank-provided ID
                "internalTransactionId": "txn-123",
                "institutionId": "REVOLUT_REVOLT21",
                "iban": "LT313250081177977789",
                "transactionDate": "2025-09-01T09:30:00Z",
                "description": "Coffee Shop Payment",
                "transactionValue": -10.50,
                "transactionCurrency": "EUR",
                "transactionStatus": "booked",
                "accountId": "test-account-123",
                "rawTransaction": {"transactionId": "txn-bank-123", "some": "raw_data"},
            }
        ]

        with (
            patch("leggen.utils.config.config", mock_config),
            patch(
                "leggen.api.routes.accounts.database_service.get_transactions_from_db",
                return_value=mock_transactions,
            ),
            patch(
                "leggen.api.routes.accounts.database_service.get_transaction_count_from_db",
                return_value=1,
            ),
        ):
            response = api_client.get(
                "/api/v1/accounts/test-account-123/transactions?summary_only=false"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1

        transaction = data["data"][0]
        assert transaction["internal_transaction_id"] == "txn-123"
        assert transaction["institution_id"] == "REVOLUT_REVOLT21"
        assert transaction["iban"] == "LT313250081177977789"
        assert "raw_transaction" in transaction

    def test_get_account_not_found(
        self, api_client, mock_config, mock_auth_token, mock_db_path
    ):
        """Test handling of non-existent account."""
        with (
            patch("leggen.utils.config.config", mock_config),
            patch(
                "leggen.api.routes.accounts.database_service.get_account_details_from_db",
                return_value=None,
            ),
        ):
            response = api_client.get("/api/v1/accounts/nonexistent")

        assert response.status_code == 404
