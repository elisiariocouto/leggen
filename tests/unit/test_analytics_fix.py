"""Tests for analytics fixes to ensure all transactions are used in statistics."""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from leggen.api.dependencies import get_transaction_repository
from leggen.commands.server import create_app


class TestAnalyticsFix:
    """Test analytics fixes for transaction limits"""

    @pytest.fixture
    def client(self):
        app = create_app()
        return TestClient(app)

    @pytest.fixture
    def mock_transaction_repo(self):
        return Mock()

    @pytest.mark.asyncio
    async def test_transaction_stats_uses_all_transactions(self, mock_transaction_repo):
        """Test that transaction stats endpoint uses all transactions (not limited to 100)"""
        # Mock data for 600 transactions (simulating the issue)
        mock_transactions = []
        for i in range(600):
            mock_transactions.append(
                {
                    "transactionId": f"txn-{i}",
                    "transactionDate": (
                        datetime.now() - timedelta(days=i % 365)
                    ).isoformat(),
                    "description": f"Transaction {i}",
                    "transactionValue": 10.0 if i % 2 == 0 else -5.0,
                    "transactionCurrency": "EUR",
                    "transactionStatus": "booked",
                    "accountId": f"account-{i % 3}",
                }
            )

        mock_transaction_repo.get_transactions.return_value = mock_transactions

        app = create_app()
        app.dependency_overrides[get_transaction_repository] = (
            lambda: mock_transaction_repo
        )
        client = TestClient(app)

        response = client.get("/api/v1/transactions/stats?days=365")

        assert response.status_code == 200
        data = response.json()

        # Verify that limit=None was passed to get all transactions
        mock_transaction_repo.get_transactions.assert_called_once()
        call_args = mock_transaction_repo.get_transactions.call_args
        assert call_args.kwargs.get("limit") is None, (
            "Stats endpoint should pass limit=None to get all transactions"
        )

        # Verify that the response contains stats for all 600 transactions
        stats = data
        assert stats["total_transactions"] == 600, (
            "Should process all 600 transactions, not just 100"
        )

        # Verify calculations are correct for all transactions
        expected_income = sum(
            txn["transactionValue"]
            for txn in mock_transactions
            if txn["transactionValue"] > 0
        )
        expected_expenses = sum(
            abs(txn["transactionValue"])
            for txn in mock_transactions
            if txn["transactionValue"] < 0
        )

        assert stats["total_income"] == expected_income
        assert stats["total_expenses"] == expected_expenses

    @pytest.mark.asyncio
    async def test_analytics_endpoint_returns_all_transactions(
        self, mock_transaction_repo
    ):
        """Test that the new analytics endpoint returns all transactions without pagination"""
        # Mock data for 600 transactions
        mock_transactions = []
        for i in range(600):
            mock_transactions.append(
                {
                    "transactionId": f"txn-{i}",
                    "transactionDate": (
                        datetime.now() - timedelta(days=i % 365)
                    ).isoformat(),
                    "description": f"Transaction {i}",
                    "transactionValue": 10.0 if i % 2 == 0 else -5.0,
                    "transactionCurrency": "EUR",
                    "transactionStatus": "booked",
                    "accountId": f"account-{i % 3}",
                }
            )

        mock_transaction_repo.get_transactions.return_value = mock_transactions

        app = create_app()
        app.dependency_overrides[get_transaction_repository] = (
            lambda: mock_transaction_repo
        )
        client = TestClient(app)

        response = client.get("/api/v1/transactions/analytics?days=365")

        assert response.status_code == 200
        data = response.json()

        # Verify that limit=None was passed to get all transactions
        mock_transaction_repo.get_transactions.assert_called_once()
        call_args = mock_transaction_repo.get_transactions.call_args
        assert call_args.kwargs.get("limit") is None, (
            "Analytics endpoint should pass limit=None"
        )

        # Verify that all 600 transactions are returned
        transactions_data = data
        assert len(transactions_data) == 600, (
            "Analytics endpoint should return all 600 transactions"
        )
