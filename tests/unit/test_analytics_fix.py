"""Regression test: statistics must cover the whole filtered history,
not just the first page of transactions."""

from datetime import datetime, timedelta

import pytest

from tests.conftest import persist_transactions


@pytest.mark.api
class TestAnalyticsFix:
    """Stats aggregation covers every matching transaction."""

    def test_transaction_stats_uses_all_transactions(self, api_client, mock_db_path):
        """600 transactions - well past any page size - are all aggregated."""
        base_date = datetime(2024, 6, 1)
        rows = [
            (
                f"txn-{i}",
                f"account-{i % 3}",
                (base_date + timedelta(minutes=i)).isoformat(),
                10.0 if i % 2 == 0 else -5.0,
                "EUR",
                "booked",
            )
            for i in range(600)
        ]
        persist_transactions(rows)

        response = api_client.get(
            "/api/v1/transactions/stats?date_from=2024-01-01&date_to=2025-06-01"
        )

        assert response.status_code == 200
        stats = response.json()

        assert stats["total_transactions"] == 600
        assert stats["total_income"] == 10.0 * 300
        assert stats["total_expenses"] == 5.0 * 300
        assert stats["accounts_included"] == 3
