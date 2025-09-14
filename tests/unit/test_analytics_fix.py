"""Tests for analytics fixes to ensure all transactions are used in statistics."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from leggen.commands.server import create_app
from leggen.services.database_service import DatabaseService


class TestAnalyticsFix:
    """Test analytics fixes for transaction limits"""

    @pytest.fixture
    def client(self):
        app = create_app()
        return TestClient(app)

    @pytest.fixture
    def mock_database_service(self):
        return Mock(spec=DatabaseService)

    @pytest.mark.asyncio
    async def test_transaction_stats_uses_all_transactions(self, mock_database_service):
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

        mock_database_service.get_transactions_from_db = AsyncMock(
            return_value=mock_transactions
        )

        # Test that the endpoint calls get_transactions_from_db with limit=None
        with patch(
            "leggen.api.routes.transactions.database_service", mock_database_service
        ):
            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/transactions/stats?days=365")

            assert response.status_code == 200
            data = response.json()

            # Verify that limit=None was passed to get all transactions
            mock_database_service.get_transactions_from_db.assert_called_once()
            call_args = mock_database_service.get_transactions_from_db.call_args
            assert call_args.kwargs.get("limit") is None, (
                "Stats endpoint should pass limit=None to get all transactions"
            )

            # Verify that the response contains stats for all 600 transactions
            assert data["success"] is True
            stats = data["data"]
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
        self, mock_database_service
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

        mock_database_service.get_transactions_from_db = AsyncMock(
            return_value=mock_transactions
        )

        with patch(
            "leggen.api.routes.transactions.database_service", mock_database_service
        ):
            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/transactions/analytics?days=365")

            assert response.status_code == 200
            data = response.json()

            # Verify that limit=None was passed to get all transactions
            mock_database_service.get_transactions_from_db.assert_called_once()
            call_args = mock_database_service.get_transactions_from_db.call_args
            assert call_args.kwargs.get("limit") is None, (
                "Analytics endpoint should pass limit=None"
            )

            # Verify that all 600 transactions are returned
            assert data["success"] is True
            transactions_data = data["data"]
            assert len(transactions_data) == 600, (
                "Analytics endpoint should return all 600 transactions"
            )
