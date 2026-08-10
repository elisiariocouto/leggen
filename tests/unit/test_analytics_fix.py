"""Regression test: statistics must cover the whole filtered history,
not just the first page of transactions."""

from datetime import datetime, timedelta

import pytest

from leggen.repositories import TransactionRepository


@pytest.mark.api
class TestAnalyticsFix:
    """Stats aggregation covers every matching transaction."""

    def test_transaction_stats_uses_all_transactions(self, api_client, mock_db_path):
        """600 transactions — well past any page size — are all aggregated."""
        base_date = datetime(2024, 6, 1)
        transactions = [
            {
                "transactionId": f"txn-{i}",
                "internalTransactionId": f"int-{i}",
                "institutionId": "TEST_BANK",
                "iban": "LT313250081177977789",
                "accountId": f"account-{i % 3}",
                "transactionDate": (
                    base_date + timedelta(minutes=i % (300 * 24 * 60))
                ).isoformat(),
                "description": f"Transaction {i}",
                "transactionValue": 10.0 if i % 2 == 0 else -5.0,
                "transactionCurrency": "EUR",
                "transactionStatus": "booked",
                "rawTransaction": {"transactionId": f"txn-{i}"},
            }
            for i in range(600)
        ]

        repo = TransactionRepository()
        for account in ("account-0", "account-1", "account-2"):
            repo.persist(
                account,
                [txn for txn in transactions if txn["accountId"] == account],
            )

        response = api_client.get(
            "/api/v1/transactions/stats?date_from=2024-01-01&date_to=2025-06-01"
        )

        assert response.status_code == 200
        stats = response.json()

        assert stats["total_transactions"] == 600
        assert stats["total_income"] == 10.0 * 300
        assert stats["total_expenses"] == 5.0 * 300
        assert stats["accounts_included"] == 3
