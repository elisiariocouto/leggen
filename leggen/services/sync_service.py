import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from loguru import logger

from leggen.api.models.sync import SyncResult
from leggen.errors import ConflictError, describe_exception
from leggen.repositories import (
    AccountRepository,
    BalanceRepository,
    SessionRepository,
    SyncRepository,
    TransactionRepository,
)
from leggen.services.data_processors import (
    enrich_account_details,
    merge_account_metadata_into_balances,
    process_transactions,
    transform_to_database_format,
)
from leggen.services.enablebanking_service import get_enablebanking_service
from leggen.services.notification_service import NotificationService
from leggen.services.rules import CategoryRuleEngine

# Constants for notification
EXPIRED_DAYS_LEFT = 0
EXPIRY_WARNING_THRESHOLDS = [7, 3, 1]

# An incremental sync re-fetches this much history so late bookings and
# status changes on recent transactions are picked up.
INCREMENTAL_SYNC_DAYS = 30


class SyncAlreadyRunningError(ConflictError):
    """Raised when a sync is triggered while another one is still running."""

    code = "SYNC_ALREADY_RUNNING"


@dataclass
class _SyncRun:
    """Everything one sync accumulates.

    Persisted as the sync_operations row when the run ends, however it ends,
    and returned to the caller as a SyncResult on success.
    """

    trigger_type: str
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    accounts_processed: int = 0
    transactions_added: int = 0
    transactions_updated: int = 0
    balances_updated: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)

    def log(self, message: str) -> None:
        """Record a progress line on the operation and in the server log."""
        logger.info(message)
        self.logs.append(message)

    def fail(self, message: str) -> None:
        """Record an error; any error makes the whole run unsuccessful."""
        logger.error(message)
        self.errors.append(message)
        self.logs.append(message)

    @property
    def success(self) -> bool:
        return not self.errors

    @property
    def duration_seconds(self) -> float:
        end = self.completed_at or datetime.now(UTC)
        return (end - self.started_at).total_seconds()

    def to_operation(self) -> dict[str, Any]:
        """The row SyncRepository.persist stores."""
        return {
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "trigger_type": self.trigger_type,
            "success": self.success,
            "accounts_processed": self.accounts_processed,
            "transactions_added": self.transactions_added,
            "transactions_updated": self.transactions_updated,
            "balances_updated": self.balances_updated,
            "duration_seconds": self.duration_seconds,
            "errors": self.errors,
            "warnings": self.warnings,
            "logs": self.logs,
        }

    def to_result(self) -> SyncResult:
        assert self.completed_at is not None
        return SyncResult(
            success=self.success,
            accounts_processed=self.accounts_processed,
            transactions_added=self.transactions_added,
            transactions_updated=self.transactions_updated,
            balances_updated=self.balances_updated,
            duration_seconds=self.duration_seconds,
            errors=self.errors,
            warnings=self.warnings,
            started_at=self.started_at,
            completed_at=self.completed_at,
        )


class SyncService:
    # Class-level so the "already running" guard holds across all instances —
    # only one sync may run per process.
    _sync_lock = asyncio.Lock()

    def __init__(self):
        self.enablebanking = get_enablebanking_service()
        self.notifications = NotificationService()

        # Repositories
        self.accounts = AccountRepository()
        self.balances = BalanceRepository()
        self.transactions = TransactionRepository()
        self.sync = SyncRepository()
        self.session_repo = SessionRepository()
        self.rules = CategoryRuleEngine()

    async def sync_all_accounts(
        self,
        full_sync: bool = False,
        trigger_type: str = "manual",
        account_ids: list[str] | None = None,
    ) -> SyncResult:
        """Sync connected accounts, optionally restricted to account_ids.

        account_ids accepts the IDs returned by GET /accounts (IBAN-based
        database IDs) as well as EnableBanking account UIDs.

        A failure on one account is recorded and the others still sync; a
        failure outside the per-account loop is recorded and re-raised.
        Either way the run leaves a sync_operations row behind.
        """
        if self._sync_lock.locked():
            raise SyncAlreadyRunningError("Sync is already running")

        async with self._sync_lock:
            run = _SyncRun(trigger_type)
            run.logs.append(f"Sync started at {run.started_at.isoformat()}")
            try:
                await self._sync(run, full_sync, account_ids)
            except Exception as e:
                run.fail(f"Sync failed: {describe_exception(e)}")
                raise
            finally:
                run.completed_at = datetime.now(UTC)
                self._record_operation(run)
            return run.to_result()

    async def _sync(
        self, run: _SyncRun, full_sync: bool, account_ids: list[str] | None
    ) -> None:
        run.log("Starting sync of all accounts")
        sessions = self.session_repo.get_sessions()
        targets = self._accounts_to_sync(sessions, account_ids, run)
        requested_ids = set(account_ids) if account_ids else None

        date_from: str | None = None
        if full_sync:
            run.logs.append("Full sync: fetching all transactions")
        else:
            since = datetime.now(UTC) - timedelta(days=INCREMENTAL_SYNC_DAYS)
            date_from = since.strftime("%Y-%m-%d")
            run.logs.append(f"Fetching transactions from {date_from}")

        await self._check_session_expiry(sessions)

        for account_id, session in targets.items():
            try:
                await self._sync_account(
                    account_id, session, requested_ids, date_from, run
                )
            except Exception as e:
                await self._report_account_failure(account_id, e, run)

        run.log(
            f"Sync completed: {run.accounts_processed} accounts, "
            f"{run.transactions_added} new transactions"
        )

    def _accounts_to_sync(
        self,
        sessions: list[dict[str, Any]],
        account_ids: list[str] | None,
        run: _SyncRun,
    ) -> dict[str, dict[str, Any]]:
        """Map each EnableBanking account UID to the session that holds it.

        Session rows store the raw EnableBanking account objects, whose IBAN
        (when present) is the database account ID. Deleted accounts are left
        out. With a per-account request, an account is kept when its UID or
        IBAN was asked for — or when its IBAN is not known locally yet, in
        which case `_sync_account` resolves it from the account details and
        makes the final call.
        """
        session_by_uid: dict[str, dict[str, Any]] = {}
        iban_by_uid: dict[str, str | None] = {}
        for session in sessions:
            for account in session.get("accounts", []) or []:
                if isinstance(account, dict):
                    uid = account.get("uid") or account.get("id")
                    iban = (account.get("account_id") or {}).get("iban")
                else:
                    uid, iban = account, None
                if uid:
                    session_by_uid[uid] = session
                    iban_by_uid[uid] = iban

        deleted_ids = {
            a["id"]
            for a in self.accounts.get_accounts(include_deleted=True)
            if a.get("status") == "DELETED"
        }
        for uid in deleted_ids:
            session_by_uid.pop(uid, None)

        if account_ids:
            requested = set(account_ids)
            session_by_uid = {
                uid: session
                for uid, session in session_by_uid.items()
                if uid in requested
                or iban_by_uid[uid] in requested
                or iban_by_uid[uid] is None
            }
            run.logs.append(f"Per-account sync requested for: {sorted(requested)}")

        run.logs.append(f"Found {len(session_by_uid)} accounts to sync")
        return session_by_uid

    async def _sync_account(
        self,
        account_id: str,
        session: dict[str, Any],
        requested_ids: set[str] | None,
        date_from: str | None,
        run: _SyncRun,
    ) -> None:
        """Fetch one account from EnableBanking and store what it returned."""
        details = await self.enablebanking.get_account_details(account_id)

        # The IBAN is the stored ID, so one real-world account stays one row
        # across providers.
        stored_id = details.get("account_id", {}).get("iban") or account_id

        # Authoritative per-account filter: accounts kept only because their
        # IBAN wasn't known locally are resolved now.
        if (
            requested_ids
            and account_id not in requested_ids
            and stored_id not in requested_ids
        ):
            logger.debug(f"Skipping account {account_id}: not in requested accounts")
            return

        account_details = {
            "id": stored_id,
            "institution_id": session["aspsp_name"],
            "status": "READY",
            "iban": details.get("account_id", {}).get("iban"),
            "name": details.get("name"),
            "currency": details.get("currency"),
            "created": session.get("created_at"),
        }

        balances = await self.enablebanking.get_account_balances(account_id)
        if balances:
            account_details = await enrich_account_details(
                account_details,
                balances,
                aspsp_country=session.get("aspsp_country"),
                enablebanking_service=self.enablebanking,
            )
            self.accounts.persist(account_details)
            self._store_balances(stored_id, account_details, balances, run)
        else:
            self.accounts.persist(account_details)

        transactions = await self.enablebanking.get_account_transactions(
            account_id, date_from=date_from
        )
        if transactions:
            await self._store_transactions(
                account_id, stored_id, account_details, transactions, run
            )

        run.accounts_processed += 1
        run.log(f"Synced account {account_id} successfully")

    def _store_balances(
        self,
        stored_id: str,
        account_details: dict[str, Any],
        balances: dict[str, Any],
        run: _SyncRun,
    ) -> None:
        with_account = merge_account_metadata_into_balances(balances, account_details)
        self.balances.persist(
            stored_id, transform_to_database_format(stored_id, with_account)
        )
        run.balances_updated += len(balances.get("balances", []))

    async def _store_transactions(
        self,
        account_id: str,
        stored_id: str,
        account_details: dict[str, Any],
        transactions: dict[str, Any],
        run: _SyncRun,
    ) -> None:
        processed, skipped_count = process_transactions(
            stored_id, account_details, transactions
        )
        if skipped_count:
            run.warnings.append(
                f"{skipped_count} transaction(s) skipped for account "
                f"{account_id} — see server logs"
            )
        new_transactions, updated_count = self.transactions.persist(
            stored_id, processed
        )
        run.transactions_added += len(new_transactions)
        run.transactions_updated += updated_count

        if new_transactions:
            await self.notifications.send_transaction_notifications(new_transactions)
            self._categorize(new_transactions, run)

    async def _report_account_failure(
        self, account_id: str, error: Exception, run: _SyncRun
    ) -> None:
        message = f"Failed to sync account {account_id}: {describe_exception(error)}"
        run.fail(message)
        try:
            await self.notifications.send_sync_failure_notification(
                {
                    "account_id": account_id,
                    "error": message,
                    "type": "account_sync_failure",
                }
            )
        except Exception as notify_err:
            logger.error(f"Failed to send sync failure notification: {notify_err}")

    def _record_operation(self, run: _SyncRun) -> None:
        """Persist the run; a failure here is logged, never raised, so the
        sync's own outcome is what reaches the caller."""
        try:
            operation_id = self.sync.persist(run.to_operation())
            logger.debug(f"Saved sync operation with ID: {operation_id}")
        except Exception as e:
            logger.error(f"Failed to persist sync operation: {e}")

    def _categorize(self, new_transactions: list[dict], run: _SyncRun) -> None:
        """Run the category rules over the transactions this sync added.

        Only the new rows: history is re-evaluated on demand through
        POST /category-rules/apply, which is what a new or edited rule
        needs. Categorization is a convenience layered on the sync, so a
        failure here is a warning on the operation, never a failed sync.
        """
        keys = [(t["accountId"], t["transactionId"]) for t in new_transactions]
        try:
            result = self.rules.run(keys=keys)
        except Exception as e:
            message = f"Category rules failed: {describe_exception(e)}"
            logger.error(message)
            run.warnings.append(message)
            return

        if result.assigned:
            run.logs.append(
                f"Category rules assigned {result.assigned} of "
                f"{result.transactions_evaluated} new transactions"
            )
        for rule_id, error in result.skipped_rules.items():
            run.warnings.append(f"Category rule {rule_id} does not compile: {error}")
        for report in result.errors.values():
            run.warnings.append(
                f"Category rule '{report.rule_name}' failed on {report.count} "
                f"transaction(s): {report.samples[0] if report.samples else 'unknown error'}"
            )

    async def _check_session_expiry(self, sessions: list[dict]) -> None:
        """Check sessions for expiry and send notifications.

        Sends a notification once when a session expires, and once per warning
        threshold (7, 3, 1 days) when the remaining validity crosses it —
        sent state is persisted so syncs don't re-notify every run.

        Args:
            sessions: List of session dictionaries to check
        """
        now = datetime.now(UTC)
        for session in sessions:
            session_id = session.get("session_id", "unknown")
            aspsp_name = session.get("aspsp_name", "unknown")
            valid_until_str = session.get("valid_until")

            if not valid_until_str:
                continue

            try:
                valid_until = datetime.fromisoformat(valid_until_str)
            except (ValueError, TypeError):
                logger.warning(
                    f"Session {session_id} has unparseable valid_until: {valid_until_str!r}"
                )
                continue
            # Timestamps stored without an offset are UTC
            if valid_until.tzinfo is None:
                valid_until = valid_until.replace(tzinfo=UTC)

            if valid_until < now:
                status = "expired"
                days_left = EXPIRED_DAYS_LEFT
                threshold = EXPIRED_DAYS_LEFT
            else:
                days_left = (valid_until - now).days
                crossed = [t for t in EXPIRY_WARNING_THRESHOLDS if days_left <= t]
                if not crossed:
                    continue
                status = "expiring"
                # Only the most urgent crossed threshold fires; skipped
                # thresholds (e.g. sync was down at day 7) don't pile up.
                threshold = min(crossed)

            if self.session_repo.was_expiry_notified(session_id, threshold):
                continue

            log = logger.warning if status == "expired" else logger.info
            log(
                f"Session {session_id} for {aspsp_name} is {status} "
                f"({days_left} day(s) left)"
            )
            await self.notifications.send_expiry_notification(
                {
                    "bank": aspsp_name,
                    "session_id": session_id,
                    "status": status,
                    "days_left": days_left,
                }
            )
            self.session_repo.mark_expiry_notified(session_id, threshold)
