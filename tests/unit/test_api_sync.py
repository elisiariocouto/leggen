"""Tests for the sync API route and per-account sync filtering."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from leggen.api.models.sync import SyncResult
from leggen.background.scheduler import scheduler
from leggen.repositories import AccountRepository
from leggen.services.sync_service import SyncAlreadyRunningError, SyncService


def _sync_result() -> SyncResult:
    now = datetime.now(timezone.utc)
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

    def test_sync_with_account_ids_forwards_them(
        self,
        fastapi_app,
        api_client,
        mock_db_path,
        mock_sync_service,
        mock_account_repo,
    ):
        mock_account_repo.get_accounts.return_value = [{"id": "IBAN1"}]
        fastapi_app.dependency_overrides[AccountRepository] = lambda: mock_account_repo

        response = api_client.post("/api/v1/sync", json={"account_ids": ["IBAN1"]})

        fastapi_app.dependency_overrides.clear()

        assert response.status_code == 200
        mock_account_repo.get_accounts.assert_called_once_with(account_ids=["IBAN1"])
        mock_sync_service.sync_all_accounts.assert_called_once_with(
            False, "api", account_ids=["IBAN1"]
        )

    def test_sync_with_unknown_account_id_returns_404(
        self,
        fastapi_app,
        api_client,
        mock_db_path,
        mock_sync_service,
        mock_account_repo,
    ):
        mock_account_repo.get_accounts.return_value = [{"id": "IBAN1"}]
        fastapi_app.dependency_overrides[AccountRepository] = lambda: mock_account_repo

        response = api_client.post(
            "/api/v1/sync", json={"account_ids": ["IBAN1", "bogus"]}
        )

        fastapi_app.dependency_overrides.clear()

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
        assert response.json()["detail"] == "Sync is already running."

    def test_sync_failure_returns_sanitized_500(
        self, fastapi_app, api_client, mock_db_path, mock_sync_service
    ):
        mock_sync_service.sync_all_accounts.side_effect = Exception(
            "sqlite3.OperationalError: /secret/path/leggen.db is locked"
        )

        response = api_client.post("/api/v1/sync")

        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to run sync."


@pytest.mark.unit
class TestPerAccountSyncFilter:
    """Test SyncService.sync_all_accounts account_ids filtering."""

    DETAILS = {
        "account-1": {
            "account_id": {"iban": "IBAN1"},
            "name": "Account One",
            "currency": "EUR",
        },
        "account-2": {
            "account_id": {"iban": "IBAN2"},
            "name": "Account Two",
            "currency": "EUR",
        },
    }

    def _session(self, accounts) -> dict:
        return {
            "session_id": "sess-123",
            "aspsp_name": "TEST_BANK",
            "aspsp_country": "PT",
            "status": "active",
            "accounts": accounts,
            "created_at": "2025-09-01T00:00:00Z",
        }

    async def _run_sync(self, sync_service, sessions, account_ids):
        with (
            patch.object(
                sync_service.session_repo, "get_sessions", return_value=sessions
            ),
            patch.object(
                sync_service.enablebanking, "get_account_details"
            ) as mock_get_details,
            patch.object(
                sync_service.enablebanking, "get_account_balances", return_value={}
            ),
            patch.object(
                sync_service.enablebanking, "get_account_transactions", return_value={}
            ),
            patch.object(sync_service.accounts, "persist") as mock_persist,
            patch.object(sync_service.sync, "persist", return_value=1),
        ):
            mock_get_details.side_effect = lambda uid: self.DETAILS[uid]

            result = await sync_service.sync_all_accounts(account_ids=account_ids)

            return result, mock_get_details, mock_persist

    @pytest.mark.asyncio
    async def test_filters_by_db_account_id(self, mock_db_path):
        """Requesting a DB account ID (IBAN) syncs only that account and
        never touches the others (their IBAN is known from the session)."""
        sessions = [
            self._session(
                [
                    {"uid": "account-1", "account_id": {"iban": "IBAN1"}},
                    {"uid": "account-2", "account_id": {"iban": "IBAN2"}},
                ]
            )
        ]

        result, mock_get_details, mock_persist = await self._run_sync(
            SyncService(), sessions, account_ids=["IBAN1"]
        )

        assert result.accounts_processed == 1
        mock_get_details.assert_called_once_with("account-1")
        mock_persist.assert_called_once()
        assert mock_persist.call_args.args[0]["id"] == "IBAN1"

    @pytest.mark.asyncio
    async def test_filters_by_enablebanking_uid(self, mock_db_path):
        """Requesting an EnableBanking UID also works."""
        sessions = [
            self._session(
                [
                    {"uid": "account-1", "account_id": {"iban": "IBAN1"}},
                    {"uid": "account-2", "account_id": {"iban": "IBAN2"}},
                ]
            )
        ]

        result, mock_get_details, mock_persist = await self._run_sync(
            SyncService(), sessions, account_ids=["account-2"]
        )

        assert result.accounts_processed == 1
        mock_get_details.assert_called_once_with("account-2")
        assert mock_persist.call_args.args[0]["id"] == "IBAN2"

    @pytest.mark.asyncio
    async def test_filters_when_session_lacks_iban(self, mock_db_path):
        """Accounts stored as plain UID strings (no local IBAN) resolve
        through account details: the requested one syncs, the rest skip."""
        sessions = [self._session(["account-1", "account-2"])]

        result, mock_get_details, mock_persist = await self._run_sync(
            SyncService(), sessions, account_ids=["IBAN1"]
        )

        # Both accounts need a details call to learn their IBAN, but only
        # the requested one is processed
        assert mock_get_details.call_count == 2
        assert result.accounts_processed == 1
        mock_persist.assert_called_once()
        assert mock_persist.call_args.args[0]["id"] == "IBAN1"

    @pytest.mark.asyncio
    async def test_no_filter_syncs_everything(self, mock_db_path):
        sessions = [
            self._session(
                [
                    {"uid": "account-1", "account_id": {"iban": "IBAN1"}},
                    {"uid": "account-2", "account_id": {"iban": "IBAN2"}},
                ]
            )
        ]

        result, mock_get_details, mock_persist = await self._run_sync(
            SyncService(), sessions, account_ids=None
        )

        assert result.accounts_processed == 2
        assert mock_get_details.call_count == 2
