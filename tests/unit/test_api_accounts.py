"""Tests for the accounts API endpoints, against the real temporary database."""

import pytest

from leggen.repositories import (
    AccountRepository,
    BalanceRepository,
    TransactionFilter,
    TransactionRepository,
)
from tests.helpers import persist_transactions

IBAN = "LT313250081177977789"


def _account(account_id: str, **overrides) -> dict:
    data = {
        "id": account_id,
        "institution_id": "REVOLUT_REVOLT21",
        "status": "READY",
        "iban": IBAN,
        "name": "Personal Account",
        "created": "2024-02-13T23:56:00Z",
        "last_accessed": "2025-09-01T09:30:00Z",
    }
    data.update(overrides)
    AccountRepository().persist(data)
    return data


def _balance(
    account_id: str,
    amount: float,
    balance_type: str = "interimAvailable",
    timestamp: str = "2025-09-01T09:30:00Z",
) -> None:
    BalanceRepository().persist(
        account_id,
        [
            (
                account_id,
                "REVOLUT_REVOLT21",
                "active",
                IBAN,
                amount,
                "EUR",
                balance_type,
                timestamp,
            )
        ],
    )


@pytest.mark.api
class TestAccountsAPI:
    def test_get_all_accounts_with_latest_balance(self, api_client):
        _account("test-account-123")
        _balance("test-account-123", 80.00, timestamp="2025-08-01T09:30:00Z")
        _balance("test-account-123", 100.50, timestamp="2025-09-01T09:30:00Z")

        response = api_client.get("/api/v1/accounts")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        account = data[0]
        assert account["id"] == "test-account-123"
        assert account["institution_id"] == "REVOLUT_REVOLT21"
        assert account["iban"] == IBAN
        # Only the newest snapshot per balance type is reported.
        assert len(account["balances"]) == 1
        assert account["balances"][0]["amount"] == 100.50
        assert account["balances"][0]["balance_type"] == "interimAvailable"

    def test_account_without_balances_has_an_empty_list(self, api_client):
        _account("no-balances")

        response = api_client.get("/api/v1/accounts")

        assert response.status_code == 200
        assert response.json()[0]["balances"] == []

    def test_update_account_display_name(self, api_client):
        _account("test-account-123")

        response = api_client.put(
            "/api/v1/accounts/test-account-123",
            json={"display_name": "My Custom Account Name"},
        )

        assert response.status_code == 204
        stored = AccountRepository().get_account("test-account-123")
        assert stored["display_name"] == "My Custom Account Name"
        # The rest of the row is untouched.
        assert stored["name"] == "Personal Account"
        assert stored["status"] == "READY"

    def test_update_account_not_found(self, api_client):
        response = api_client.put(
            "/api/v1/accounts/nonexistent",
            json={"display_name": "New Name"},
        )

        assert response.status_code == 404

    def test_delete_account_removes_its_data(self, api_client):
        _account("test-account-123")
        _balance("test-account-123", 100.50)
        persist_transactions(
            [
                (
                    "txn-1",
                    "test-account-123",
                    "2025-09-01T10:00:00",
                    -5.0,
                    "EUR",
                    "booked",
                )
            ]
        )

        response = api_client.delete("/api/v1/accounts/test-account-123")

        assert response.status_code == 204
        # Soft-deleted: the row stays, flagged, but its data is gone.
        assert AccountRepository().get_account("test-account-123")["status"] == (
            "DELETED"
        )
        assert (
            TransactionRepository().get_count(
                TransactionFilter(account_id="test-account-123")
            )
            == 0
        )
        assert BalanceRepository().get_balances("test-account-123") == []

    def test_delete_account_keep_data(self, api_client):
        _account("test-account-123")
        _balance("test-account-123", 100.50)
        persist_transactions(
            [
                (
                    "txn-1",
                    "test-account-123",
                    "2025-09-01T10:00:00",
                    -5.0,
                    "EUR",
                    "booked",
                )
            ]
        )

        response = api_client.delete(
            "/api/v1/accounts/test-account-123?delete_data=false"
        )

        assert response.status_code == 204
        assert AccountRepository().get_account("test-account-123")["status"] == (
            "DELETED"
        )
        assert (
            TransactionRepository().get_count(
                TransactionFilter(account_id="test-account-123")
            )
            == 1
        )
        assert len(BalanceRepository().get_balances("test-account-123")) == 1

    def test_delete_account_not_found(self, api_client):
        response = api_client.delete("/api/v1/accounts/nonexistent")

        assert response.status_code == 404

    def test_deleted_account_still_returned(self, api_client):
        """Soft-deleted accounts still appear in GET /accounts, flagged."""
        _account("active-account")
        _account("deleted-account", iban="LT313250081177977790")
        api_client.delete("/api/v1/accounts/deleted-account")

        response = api_client.get("/api/v1/accounts")

        assert response.status_code == 200
        statuses = {a["id"]: a["status"] for a in response.json()}
        assert statuses == {"active-account": "READY", "deleted-account": "DELETED"}
