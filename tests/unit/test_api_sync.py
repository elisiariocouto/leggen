"""Tests for the sync API route and per-account sync filtering."""

import tomllib
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from leggen.api.models.sync import SyncResult
from leggen.background.scheduler import scheduler
from leggen.repositories import AccountRepository
from leggen.services.sync_service import SyncAlreadyRunningError, SyncService
from tests.helpers import account_details, enablebanking_returns, seed_session


def _sync_result() -> SyncResult:
    now = datetime.now(UTC)
    return SyncResult(
        success=True,
        accounts_processed=1,
        transactions_added=2,
        transactions_updated=0,
        balances_updated=1,
        duration_seconds=0.5,
        errors=[],
        started_at=now,
        completed_at=now,
    )


def _persist_account(account_id: str) -> None:
    AccountRepository().persist(
        {
            "id": account_id,
            "institution_id": "TEST_BANK",
            "status": "READY",
            "iban": account_id,
            "created": "2025-01-01T00:00:00Z",
        }
    )


@pytest.fixture
def mock_sync_service():
    """Replace the scheduler's sync service with a mock for route tests."""
    mock_service = MagicMock()
    mock_service.sync_all_accounts = AsyncMock(return_value=_sync_result())
    scheduler.sync_service = mock_service
    yield mock_service
    scheduler._sync_service = None


@pytest.mark.api
class TestSyncAPI:
    """Test POST /sync account_ids handling."""

    def test_sync_all_accounts_when_no_body(
        self, fastapi_app, api_client, mock_db_path, mock_sync_service
    ):
        response = api_client.post("/api/v1/sync")

        assert response.status_code == 200
        mock_sync_service.sync_all_accounts.assert_called_once_with(
            False, "api", account_ids=None
        )

    def test_sync_with_account_ids_forwards_them(self, api_client, mock_sync_service):
        _persist_account("IBAN1")

        response = api_client.post("/api/v1/sync", json={"account_ids": ["IBAN1"]})

        assert response.status_code == 200
        mock_sync_service.sync_all_accounts.assert_called_once_with(
            False, "api", account_ids=["IBAN1"]
        )

    def test_sync_with_unknown_account_id_returns_404(
        self, api_client, mock_sync_service
    ):
        _persist_account("IBAN1")

        response = api_client.post(
            "/api/v1/sync", json={"account_ids": ["IBAN1", "bogus"]}
        )

        assert response.status_code == 404
        assert "bogus" in response.json()["detail"]
        mock_sync_service.sync_all_accounts.assert_not_called()

    def test_sync_with_empty_account_ids_syncs_all(
        self, fastapi_app, api_client, mock_db_path, mock_sync_service
    ):
        response = api_client.post(
            "/api/v1/sync", json={"account_ids": [], "full_sync": True}
        )

        assert response.status_code == 200
        mock_sync_service.sync_all_accounts.assert_called_once_with(
            True, "api", account_ids=None
        )

    def test_sync_already_running_returns_409(
        self, fastapi_app, api_client, mock_db_path, mock_sync_service
    ):
        mock_sync_service.sync_all_accounts.side_effect = SyncAlreadyRunningError(
            "Sync is already running"
        )

        response = api_client.post("/api/v1/sync")

        assert response.status_code == 409
        body = response.json()
        assert body["detail"] == "Sync is already running"
        assert body["code"] == "SYNC_ALREADY_RUNNING"

    def test_sync_failure_returns_sanitized_500(
        self, fastapi_app, mock_db_path, mock_sync_service, raw_api_client
    ):
        mock_sync_service.sync_all_accounts.side_effect = Exception(
            "sqlite3.OperationalError: /secret/path/leggen.db is locked"
        )

        response = raw_api_client.post("/api/v1/sync")

        assert response.status_code == 500
        assert response.json()["detail"] == "Internal server error."
        assert "/secret/path" not in response.text


@pytest.mark.api
class TestSyncScheduleAPI:
    """Test PUT /sync/schedule config handling."""

    def test_update_sync_schedule_preserves_backup_schedule(
        self, api_client, test_config
    ):
        """Updating the sync schedule must not reset scheduler.backup
        to defaults (regression: update_section replaced the whole section)."""
        custom_backup = {"enabled": False, "hour": 12, "minute": 30}
        scheduler_section = dict(test_config.scheduler_config)
        scheduler_section["backup"] = custom_backup
        test_config.update_section("scheduler", scheduler_section)

        response = api_client.put(
            "/api/v1/sync/schedule", json={"enabled": True, "hour": 5, "minute": 15}
        )

        assert response.status_code == 200
        assert response.json()["hour"] == 5

        backup = test_config.scheduler_config["backup"]
        assert backup["enabled"] is False
        assert backup["hour"] == 12
        assert backup["minute"] == 30

        # The surviving backup schedule must also be on disk
        with open(test_config._config_path, "rb") as f:
            on_disk = tomllib.load(f)
        assert on_disk["scheduler"]["backup"] == custom_backup
        assert on_disk["scheduler"]["sync"]["hour"] == 5


@pytest.mark.unit
class TestPerAccountSyncFilter:
    """Test SyncService.sync_all_accounts account_ids filtering."""

    DETAILS = {
        "account-1": account_details("account-1", "IBAN1", name="Account One"),
        "account-2": account_details("account-2", "IBAN2", name="Account Two"),
    }

    async def _run_sync(self, sync_service, accounts, account_ids):
        """Sync one session holding `accounts`; returns the result, the
        account-details mock and the IDs of the accounts now stored."""
        seed_session(accounts, session_id="sess-123")
        with enablebanking_returns(sync_service, details=self.DETAILS) as details:
            result = await sync_service.sync_all_accounts(account_ids=account_ids)
        stored = sorted(a["id"] for a in AccountRepository().get_accounts())
        return result, details, stored

    async def test_filters_by_db_account_id(self, mock_db_path):
        """Requesting a DB account ID (IBAN) syncs only that account and
        never touches the others (their IBAN is known from the session)."""
        accounts = [
            {"uid": "account-1", "account_id": {"iban": "IBAN1"}},
            {"uid": "account-2", "account_id": {"iban": "IBAN2"}},
        ]

        result, mock_get_details, stored = await self._run_sync(
            SyncService(), accounts, account_ids=["IBAN1"]
        )

        assert result.accounts_processed == 1
        mock_get_details.assert_called_once_with("account-1")
        assert stored == ["IBAN1"]

    async def test_filters_by_enablebanking_uid(self, mock_db_path):
        """Requesting an EnableBanking UID also works."""
        accounts = [
            {"uid": "account-1", "account_id": {"iban": "IBAN1"}},
            {"uid": "account-2", "account_id": {"iban": "IBAN2"}},
        ]

        result, mock_get_details, stored = await self._run_sync(
            SyncService(), accounts, account_ids=["account-2"]
        )

        assert result.accounts_processed == 1
        mock_get_details.assert_called_once_with("account-2")
        assert stored == ["IBAN2"]

    async def test_filters_when_session_lacks_iban(self, mock_db_path):
        """Accounts stored as plain UID strings (no local IBAN) resolve
        through account details: the requested one syncs, the rest skip."""
        accounts = ["account-1", "account-2"]

        result, mock_get_details, stored = await self._run_sync(
            SyncService(), accounts, account_ids=["IBAN1"]
        )

        # Both accounts need a details call to learn their IBAN, but only
        # the requested one is processed
        assert mock_get_details.call_count == 2
        assert result.accounts_processed == 1
        assert stored == ["IBAN1"]

    async def test_no_filter_syncs_everything(self, mock_db_path):
        accounts = [
            {"uid": "account-1", "account_id": {"iban": "IBAN1"}},
            {"uid": "account-2", "account_id": {"iban": "IBAN2"}},
        ]

        result, mock_get_details, stored = await self._run_sync(
            SyncService(), accounts, account_ids=None
        )

        assert result.accounts_processed == 2
        assert mock_get_details.call_count == 2

    def test_invalid_cron_is_rejected_before_saving(self, api_client, test_config):
        """A bad expression used to be persisted with a 200 and a null next
        run, which silently disabled scheduled syncs."""
        before = dict(test_config.scheduler_config.get("sync", {}))

        response = api_client.put(
            "/api/v1/sync/schedule",
            json={"enabled": True, "hour": 3, "minute": 0, "cron": "not a cron"},
        )

        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "INVALID_SCHEDULE"
        assert "five fields" in body["detail"]
        assert test_config.scheduler_config.get("sync", {}) == before

    def test_out_of_range_hour_is_a_validation_error(self, api_client):
        response = api_client.put(
            "/api/v1/sync/schedule", json={"enabled": True, "hour": 24, "minute": 0}
        )

        assert response.status_code == 422
        assert response.json()["code"] == "VALIDATION_ERROR"
