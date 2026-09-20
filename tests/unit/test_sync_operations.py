"""The sync_operations row every sync leaves behind, for each outcome.

The record is what the sync history page shows, so it is asserted here as
stored state rather than through the service's return value alone.
"""

from unittest.mock import patch

import pytest

from leggen.repositories import SyncRepository
from leggen.services.sync_service import SyncService
from tests.helpers import (
    account_details,
    bank_transaction,
    enablebanking_returns,
    seed_session,
)


@pytest.mark.unit
class TestSyncOperationRecord:
    async def test_successful_sync_is_recorded(self, mock_db_path):
        seed_session(["account-1"])
        service = SyncService()

        with enablebanking_returns(
            service,
            details={"account-1": account_details("account-1", "PT1")},
            transactions=[bank_transaction("tx-1", "COFFEE", "3.00")],
        ):
            result = await service.sync_all_accounts(False, "api")

        repo = SyncRepository()
        assert repo.get_operations_count() == 1
        [operation] = repo.get_operations()
        assert operation["success"] is True
        assert operation["trigger_type"] == "api"
        assert operation["accounts_processed"] == 1
        assert operation["transactions_added"] == 1
        assert operation["errors"] == []
        assert operation["warnings"] == []
        assert operation["duration_seconds"] == result.duration_seconds
        assert operation["completed_at"] is not None
        assert any("Synced account account-1" in line for line in operation["logs"])

    async def test_account_failure_is_recorded_as_failed(self, mock_db_path):
        seed_session(["account-1"])
        service = SyncService()

        with enablebanking_returns(service, details=Exception("API Error")):
            result = await service.sync_all_accounts()

        [operation] = SyncRepository().get_operations()
        assert result.success is False
        assert operation["success"] is False
        assert operation["trigger_type"] == "manual"
        assert operation["accounts_processed"] == 0
        assert len(operation["errors"]) == 1
        assert "API Error" in operation["errors"][0]

    async def test_crash_before_the_accounts_is_recorded_and_reraised(
        self, mock_db_path
    ):
        """A failure outside the per-account loop still leaves a row."""
        service = SyncService()

        with (
            patch.object(
                service.session_repo,
                "get_sessions",
                side_effect=RuntimeError("db is locked"),
            ),
            pytest.raises(RuntimeError),
        ):
            await service.sync_all_accounts()

        [operation] = SyncRepository().get_operations()
        assert operation["success"] is False
        assert operation["accounts_processed"] == 0
        assert "db is locked" in operation["errors"][0]

    async def test_operations_are_listed_newest_first(self, mock_db_path):
        seed_session([])
        service = SyncService()
        await service.sync_all_accounts(False, "scheduled")
        await service.sync_all_accounts(False, "api")

        repo = SyncRepository()
        assert repo.get_operations_count() == 2
        assert [op["trigger_type"] for op in repo.get_operations()] == [
            "api",
            "scheduled",
        ]
        assert [op["trigger_type"] for op in repo.get_operations(limit=1)] == ["api"]
