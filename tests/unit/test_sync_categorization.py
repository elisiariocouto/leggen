"""Tests for the rule engine running as part of a sync."""

from unittest.mock import patch

import pytest

from leggen.repositories import CategoryRepository, CategoryRuleRepository
from leggen.repositories.db import get_db_connection
from leggen.services.sync_service import SyncService
from tests.helpers import (
    account_details,
    bank_transaction,
    category_id,
    enablebanking_returns,
    seed_session,
)


def _assignments() -> dict[str, tuple[int, str]]:
    with get_db_connection(row_factory=True) as conn:
        rows = conn.execute(
            "SELECT transactionId, categoryId, source FROM transaction_categories"
        ).fetchall()
        return {r["transactionId"]: (r["categoryId"], r["source"]) for r in rows}


async def _sync(sync_service: SyncService, transactions: list[dict]):
    seed_session(["account-1"])
    with enablebanking_returns(
        sync_service,
        details={"account-1": account_details("account-1", "PT1")},
        transactions=transactions,
    ):
        return await sync_service.sync_all_accounts()


@pytest.mark.unit
class TestSyncCategorization:
    async def test_new_transactions_are_categorized(self, mock_db_path):
        CategoryRuleRepository().create_rule(
            "Groceries",
            category_id("Groceries"),
            'return contains(tx.description, "pingo")',
        )

        result = await _sync(
            SyncService(),
            [
                bank_transaction("tx-1", "COMPRA PINGO DOCE", "30.00"),
                bank_transaction("tx-2", "SOMETHING ELSE", "5.00"),
            ],
        )

        assert result.success is True
        assert result.transactions_added == 2
        assert _assignments() == {"tx-1": (category_id("Groceries"), "rule")}

    async def test_only_new_transactions_are_evaluated(self, mock_db_path):
        """A transaction that already existed is not re-categorized by the
        sync — that is what the explicit apply is for."""
        sync_service = SyncService()
        await _sync(
            sync_service, [bank_transaction("tx-1", "COMPRA PINGO DOCE", "30.00")]
        )
        CategoryRuleRepository().create_rule(
            "Groceries",
            category_id("Groceries"),
            'return contains(tx.description, "pingo")',
        )

        await _sync(
            sync_service, [bank_transaction("tx-1", "COMPRA PINGO DOCE", "30.00")]
        )

        assert _assignments() == {}

    async def test_manual_category_survives_a_sync(self, mock_db_path):
        sync_service = SyncService()
        await _sync(
            sync_service, [bank_transaction("tx-1", "COMPRA PINGO DOCE", "30.00")]
        )
        CategoryRepository().assign_category("PT1", "tx-1", category_id("Dining"))
        CategoryRuleRepository().create_rule(
            "Groceries", category_id("Groceries"), "return true"
        )

        # The bank re-sends the row, now booked instead of pending.
        booked = bank_transaction("tx-1", "COMPRA PINGO DOCE", "30.00")
        booked["status"] = "BOOK"
        await _sync(sync_service, [booked])

        assert _assignments() == {"tx-1": (category_id("Dining"), "manual")}

    async def test_rule_failures_become_warnings(self, mock_db_path):
        CategoryRuleRepository().create_rule(
            "Faulty", category_id("Groceries"), "return tx.raw.a.b == 1"
        )

        result = await _sync(SyncService(), [bank_transaction("tx-1", "X", "1.00")])

        assert result.success is True
        assert any("Faulty" in w for w in result.warnings)

    async def test_engine_crash_does_not_fail_the_sync(self, mock_db_path):
        sync_service = SyncService()

        with patch.object(sync_service.rules, "run", side_effect=RuntimeError("boom")):
            result = await _sync(sync_service, [bank_transaction("tx-1", "X", "1.00")])

        assert result.success is True
        assert result.transactions_added == 1
        assert any("Category rules failed" in w for w in result.warnings)
