"""Tests for the rule engine running as part of a sync."""

from unittest.mock import patch

import pytest

from leggen.repositories import CategoryRepository, CategoryRuleRepository
from leggen.repositories.db import get_db_connection
from leggen.services.sync_service import SyncService


def _category(name: str) -> int:
    return next(
        c for c in CategoryRepository().get_all_categories() if c["name"] == name
    )["id"]


def _bank_transaction(transaction_id: str, description: str, amount: str) -> dict:
    """One transaction in EnableBanking's own format."""
    return {
        "transaction_id": transaction_id,
        "entry_reference": f"ref-{transaction_id}",
        "booking_date": "2025-09-01",
        "transaction_amount": {"amount": amount, "currency": "EUR"},
        "credit_debit_indicator": "DBIT",
        "remittance_information": [description],
        "status": "BOOK",
    }


def _assignments() -> dict[str, tuple[int, str]]:
    with get_db_connection(row_factory=True) as conn:
        rows = conn.execute(
            "SELECT transactionId, categoryId, source FROM transaction_categories"
        ).fetchall()
        return {r["transactionId"]: (r["categoryId"], r["source"]) for r in rows}


async def _sync(sync_service: SyncService, transactions: list[dict]):
    with (
        patch.object(sync_service.session_repo, "get_sessions") as mock_sessions,
        patch.object(sync_service.enablebanking, "get_account_details") as mock_details,
        patch.object(
            sync_service.enablebanking, "get_account_balances", return_value={}
        ),
        patch.object(
            sync_service.enablebanking,
            "get_account_transactions",
            return_value={"transactions": transactions},
        ),
        patch.object(sync_service.notifications, "send_transaction_notifications"),
        patch.object(sync_service.notifications, "send_sync_failure_notification"),
    ):
        mock_sessions.return_value = [
            {
                "session_id": "sess-1",
                "aspsp_name": "TEST_BANK",
                "aspsp_country": "PT",
                "status": "active",
                "accounts": ["account-1"],
                "created_at": "2025-09-01T00:00:00Z",
            }
        ]
        mock_details.return_value = {
            "uid": "account-1",
            "account_id": {"iban": "PT1"},
            "name": "Test Account",
            "currency": "EUR",
        }
        return await sync_service.sync_all_accounts()


@pytest.mark.unit
class TestSyncCategorization:
    async def test_new_transactions_are_categorized(self, mock_db_path):
        CategoryRuleRepository().create_rule(
            "Groceries",
            _category("Groceries"),
            'return contains(tx.description, "pingo")',
        )

        result = await _sync(
            SyncService(),
            [
                _bank_transaction("tx-1", "COMPRA PINGO DOCE", "30.00"),
                _bank_transaction("tx-2", "SOMETHING ELSE", "5.00"),
            ],
        )

        assert result.success is True
        assert result.transactions_added == 2
        assert _assignments() == {"tx-1": (_category("Groceries"), "rule")}

    async def test_only_new_transactions_are_evaluated(self, mock_db_path):
        """A transaction that already existed is not re-categorized by the
        sync — that is what the explicit apply is for."""
        sync_service = SyncService()
        await _sync(
            sync_service, [_bank_transaction("tx-1", "COMPRA PINGO DOCE", "30.00")]
        )
        CategoryRuleRepository().create_rule(
            "Groceries",
            _category("Groceries"),
            'return contains(tx.description, "pingo")',
        )

        await _sync(
            sync_service, [_bank_transaction("tx-1", "COMPRA PINGO DOCE", "30.00")]
        )

        assert _assignments() == {}

    async def test_manual_category_survives_a_sync(self, mock_db_path):
        sync_service = SyncService()
        await _sync(
            sync_service, [_bank_transaction("tx-1", "COMPRA PINGO DOCE", "30.00")]
        )
        CategoryRepository().assign_category("PT1", "tx-1", _category("Dining"))
        CategoryRuleRepository().create_rule(
            "Groceries", _category("Groceries"), "return true"
        )

        # The bank re-sends the row, now booked instead of pending.
        booked = _bank_transaction("tx-1", "COMPRA PINGO DOCE", "30.00")
        booked["status"] = "BOOK"
        await _sync(sync_service, [booked])

        assert _assignments() == {"tx-1": (_category("Dining"), "manual")}

    async def test_rule_failures_become_warnings(self, mock_db_path):
        CategoryRuleRepository().create_rule(
            "Faulty", _category("Groceries"), "return tx.raw.a.b == 1"
        )

        result = await _sync(SyncService(), [_bank_transaction("tx-1", "X", "1.00")])

        assert result.success is True
        assert any("Faulty" in w for w in result.warnings)

    async def test_engine_crash_does_not_fail_the_sync(self, mock_db_path):
        sync_service = SyncService()

        with patch.object(sync_service.rules, "run", side_effect=RuntimeError("boom")):
            result = await _sync(sync_service, [_bank_transaction("tx-1", "X", "1.00")])

        assert result.success is True
        assert result.transactions_added == 1
        assert any("Category rules failed" in w for w in result.warnings)
