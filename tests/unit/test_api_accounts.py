"""Tests for accounts API endpoints."""
import pytest
import respx
import httpx
from unittest.mock import patch


@pytest.mark.api
class TestAccountsAPI:
    """Test account-related API endpoints."""
    
    @respx.mock
    def test_get_all_accounts_success(self, api_client, mock_config, mock_auth_token, sample_account_data):
        """Test successful retrieval of all accounts."""
        requisitions_data = {
            "results": [
                {
                    "id": "req-123", 
                    "accounts": ["test-account-123"]
                }
            ]
        }
        
        balances_data = {
            "balances": [
                {
                    "balanceAmount": {"amount": "100.50", "currency": "EUR"},
                    "balanceType": "interimAvailable",
                    "lastChangeDateTime": "2025-09-01T09:30:00Z"
                }
            ]
        }
        
        # Mock GoCardless token creation
        respx.post("https://bankaccountdata.gocardless.com/api/v2/token/new/").mock(
            return_value=httpx.Response(200, json={"access": "test-token", "refresh": "test-refresh"})
        )
        
        # Mock GoCardless API calls
        respx.get("https://bankaccountdata.gocardless.com/api/v2/requisitions/").mock(
            return_value=httpx.Response(200, json=requisitions_data)
        )
        respx.get("https://bankaccountdata.gocardless.com/api/v2/accounts/test-account-123/").mock(
            return_value=httpx.Response(200, json=sample_account_data)
        )
        respx.get("https://bankaccountdata.gocardless.com/api/v2/accounts/test-account-123/balances/").mock(
            return_value=httpx.Response(200, json=balances_data)
        )
        
        with patch('leggend.config.config', mock_config):
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

    @respx.mock
    def test_get_account_details_success(self, api_client, mock_config, mock_auth_token, sample_account_data):
        """Test successful retrieval of specific account details."""
        balances_data = {
            "balances": [
                {
                    "balanceAmount": {"amount": "250.75", "currency": "EUR"},
                    "balanceType": "interimAvailable"
                }
            ]
        }
        
        # Mock GoCardless token creation
        respx.post("https://bankaccountdata.gocardless.com/api/v2/token/new/").mock(
            return_value=httpx.Response(200, json={"access": "test-token", "refresh": "test-refresh"})
        )
        
        # Mock GoCardless API calls
        respx.get("https://bankaccountdata.gocardless.com/api/v2/accounts/test-account-123/").mock(
            return_value=httpx.Response(200, json=sample_account_data)
        )
        respx.get("https://bankaccountdata.gocardless.com/api/v2/accounts/test-account-123/balances/").mock(
            return_value=httpx.Response(200, json=balances_data)
        )
        
        with patch('leggend.config.config', mock_config):
            response = api_client.get("/api/v1/accounts/test-account-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        account = data["data"]
        assert account["id"] == "test-account-123"
        assert account["iban"] == "LT313250081177977789"
        assert len(account["balances"]) == 1

    @respx.mock
    def test_get_account_balances_success(self, api_client, mock_config, mock_auth_token):
        """Test successful retrieval of account balances."""
        balances_data = {
            "balances": [
                {
                    "balanceAmount": {"amount": "1000.00", "currency": "EUR"},
                    "balanceType": "interimAvailable",
                    "lastChangeDateTime": "2025-09-01T10:00:00Z"
                },
                {
                    "balanceAmount": {"amount": "950.00", "currency": "EUR"}, 
                    "balanceType": "expected"
                }
            ]
        }
        
        # Mock GoCardless token creation
        respx.post("https://bankaccountdata.gocardless.com/api/v2/token/new/").mock(
            return_value=httpx.Response(200, json={"access": "test-token", "refresh": "test-refresh"})
        )
        
        # Mock GoCardless API
        respx.get("https://bankaccountdata.gocardless.com/api/v2/accounts/test-account-123/balances/").mock(
            return_value=httpx.Response(200, json=balances_data)
        )
        
        with patch('leggend.config.config', mock_config):
            response = api_client.get("/api/v1/accounts/test-account-123/balances")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2
        assert data["data"][0]["amount"] == 1000.00
        assert data["data"][0]["currency"] == "EUR"
        assert data["data"][0]["balance_type"] == "interimAvailable"

    @respx.mock
    def test_get_account_transactions_success(self, api_client, mock_config, mock_auth_token, sample_account_data, sample_transaction_data):
        """Test successful retrieval of account transactions."""
        # Mock GoCardless token creation
        respx.post("https://bankaccountdata.gocardless.com/api/v2/token/new/").mock(
            return_value=httpx.Response(200, json={"access": "test-token", "refresh": "test-refresh"})
        )
        
        # Mock GoCardless API calls
        respx.get("https://bankaccountdata.gocardless.com/api/v2/accounts/test-account-123/").mock(
            return_value=httpx.Response(200, json=sample_account_data)
        )
        respx.get("https://bankaccountdata.gocardless.com/api/v2/accounts/test-account-123/transactions/").mock(
            return_value=httpx.Response(200, json=sample_transaction_data)
        )
        
        with patch('leggend.config.config', mock_config):
            response = api_client.get("/api/v1/accounts/test-account-123/transactions?summary_only=true")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        
        transaction = data["data"][0]
        assert transaction["internal_transaction_id"] == "txn-123"
        assert transaction["amount"] == -10.50
        assert transaction["currency"] == "EUR"
        assert transaction["description"] == "Coffee Shop Payment"

    @respx.mock
    def test_get_account_transactions_full_details(self, api_client, mock_config, mock_auth_token, sample_account_data, sample_transaction_data):
        """Test retrieval of full transaction details."""
        # Mock GoCardless token creation
        respx.post("https://bankaccountdata.gocardless.com/api/v2/token/new/").mock(
            return_value=httpx.Response(200, json={"access": "test-token", "refresh": "test-refresh"})
        )
        
        # Mock GoCardless API calls
        respx.get("https://bankaccountdata.gocardless.com/api/v2/accounts/test-account-123/").mock(
            return_value=httpx.Response(200, json=sample_account_data)
        )
        respx.get("https://bankaccountdata.gocardless.com/api/v2/accounts/test-account-123/transactions/").mock(
            return_value=httpx.Response(200, json=sample_transaction_data)
        )
        
        with patch('leggend.config.config', mock_config):
            response = api_client.get("/api/v1/accounts/test-account-123/transactions?summary_only=false")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        
        transaction = data["data"][0]
        assert transaction["internal_transaction_id"] == "txn-123"
        assert transaction["institution_id"] == "REVOLUT_REVOLT21"
        assert transaction["iban"] == "LT313250081177977789"
        assert "raw_transaction" in transaction

    def test_get_account_not_found(self, api_client, mock_config, mock_auth_token):
        """Test handling of non-existent account."""
        # Mock 404 response from GoCardless
        with respx.mock:
            # Mock GoCardless token creation
            respx.post("https://bankaccountdata.gocardless.com/api/v2/token/new/").mock(
                return_value=httpx.Response(200, json={"access": "test-token", "refresh": "test-refresh"})
            )
            
            respx.get("https://bankaccountdata.gocardless.com/api/v2/accounts/nonexistent/").mock(
                return_value=httpx.Response(404, json={"detail": "Account not found"})
            )
            
            with patch('leggend.config.config', mock_config):
                response = api_client.get("/api/v1/accounts/nonexistent")
            
            assert response.status_code == 404