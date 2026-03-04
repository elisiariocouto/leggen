from datetime import datetime, timedelta, timezone
from typing import List, Optional

from loguru import logger

from leggen.api.models.sync import SyncResult, SyncStatus
from leggen.repositories import (
    AccountRepository,
    BalanceRepository,
    SessionRepository,
    SyncRepository,
    TransactionRepository,
    ensure_tables,
)
from leggen.services.data_processors import (
    AccountEnricher,
    merge_account_metadata_into_balances,
    process_transactions,
    transform_to_database_format,
)
from leggen.services.enablebanking_service import EnableBankingService
from leggen.services.notification_service import NotificationService

# Constants for notification
EXPIRED_DAYS_LEFT = 0


class SyncService:
    def __init__(self):
        self.enablebanking = EnableBankingService()
        self.notifications = NotificationService()

        # Ensure all tables exist (for CLI usage outside FastAPI lifespan)
        ensure_tables()

        # Repositories
        self.accounts = AccountRepository()
        self.balances = BalanceRepository()
        self.transactions = TransactionRepository()
        self.sync = SyncRepository()
        self.session_repo = SessionRepository()

        # Data processors
        self.account_enricher = AccountEnricher()

        self._sync_status = SyncStatus(is_running=False)

    async def get_sync_status(self) -> SyncStatus:
        """Get current sync status"""
        return self._sync_status

    async def sync_all_accounts(
        self, full_sync: bool = False, trigger_type: str = "manual"
    ) -> SyncResult:
        """Sync all connected accounts"""
        if self._sync_status.is_running:
            raise Exception("Sync is already running")

        start_time = datetime.now()
        self._sync_status.is_running = True
        self._sync_status.errors = []

        accounts_processed = 0
        transactions_added = 0
        transactions_updated = 0
        balances_updated = 0
        errors = []
        logs = [f"Sync started at {start_time.isoformat()}"]

        # Initialize sync operation record
        sync_operation = {
            "started_at": start_time.isoformat(),
            "trigger_type": trigger_type,
            "accounts_processed": 0,
            "transactions_added": 0,
            "transactions_updated": 0,
            "balances_updated": 0,
            "errors": [],
            "logs": logs,
        }

        operation_id = None

        try:
            logger.info("Starting sync of all accounts")
            logs.append("Starting sync of all accounts")

            # Get all sessions from local DB
            sessions = self.session_repo.get_sessions()

            # Build account-to-session mapping
            account_session_map = {}
            all_account_ids = set()
            for session in sessions:
                session_accounts = session.get("accounts", []) or []
                for account in session_accounts:
                    if isinstance(account, dict):
                        uid = account.get("uid") or account.get("id")
                    else:
                        uid = account
                    if uid:
                        all_account_ids.add(uid)
                        account_session_map[uid] = session

            self._sync_status.total_accounts = len(all_account_ids)
            logs.append(f"Found {len(all_account_ids)} accounts to sync")

            date_from: Optional[str] = None
            if not full_sync:
                date_from = (datetime.now(timezone.utc) - timedelta(days=30)).strftime(
                    "%Y-%m-%d"
                )
                logs.append(f"Fetching transactions from {date_from}")
            else:
                logs.append("Full sync: fetching all transactions")

            # Check for expired sessions
            await self._check_session_expiry(sessions)

            # Process each account
            for account_id in all_account_ids:
                try:
                    session = account_session_map[account_id]

                    # Get account details from EnableBanking
                    details = await self.enablebanking.get_account_details(account_id)

                    # Use IBAN as stored ID to prevent duplicates across providers
                    stored_id = details.get("account_id", {}).get("iban") or account_id

                    # Map to internal format
                    account_details = {
                        "id": stored_id,
                        "institution_id": session["aspsp_name"],
                        "status": "READY",
                        "iban": details.get("account_id", {}).get("iban"),
                        "name": details.get("name"),
                        "currency": details.get("currency"),
                        "created": session.get("created_at"),
                    }

                    # Get balances
                    balances = await self.enablebanking.get_account_balances(account_id)

                    # Enrich and persist account details
                    if account_details and balances:
                        enriched_account_details = (
                            await self.account_enricher.enrich_account_details(
                                account_details,
                                balances,
                                aspsp_country=session.get("aspsp_country"),
                            )
                        )

                        self.accounts.persist(enriched_account_details)

                        balances_with_account_info = (
                            merge_account_metadata_into_balances(
                                balances, enriched_account_details
                            )
                        )
                        balance_rows = transform_to_database_format(
                            stored_id, balances_with_account_info
                        )
                        self.balances.persist(stored_id, balance_rows)
                        balances_updated += len(balances.get("balances", []))
                    elif account_details:
                        self.accounts.persist(account_details)

                    # Get and save transactions
                    transactions = await self.enablebanking.get_account_transactions(
                        account_id, date_from=date_from
                    )
                    if transactions:
                        processed_transactions = process_transactions(
                            stored_id, account_details, transactions
                        )
                        new_transactions = self.transactions.persist(
                            stored_id, processed_transactions
                        )
                        transactions_added += len(new_transactions)

                        # Send notifications for new transactions
                        if new_transactions:
                            await self.notifications.send_transaction_notifications(
                                new_transactions
                            )

                    accounts_processed += 1
                    self._sync_status.accounts_synced = accounts_processed

                    logger.info(f"Synced account {account_id} successfully")
                    logs.append(f"Synced account {account_id} successfully")

                except Exception as e:
                    error_msg = f"Failed to sync account {account_id}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    logs.append(error_msg)

                    # Send notification for account sync failure
                    try:
                        await self.notifications.send_sync_failure_notification(
                            {
                                "account_id": account_id,
                                "error": error_msg,
                                "type": "account_sync_failure",
                            }
                        )
                    except Exception as notify_err:
                        logger.error(
                            f"Failed to send sync failure notification: {notify_err}"
                        )

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            self._sync_status.last_sync = end_time

            # Update sync operation with final results
            sync_operation.update(
                {
                    "completed_at": end_time.isoformat(),
                    "success": len(errors) == 0,
                    "accounts_processed": accounts_processed,
                    "transactions_added": transactions_added,
                    "transactions_updated": transactions_updated,
                    "balances_updated": balances_updated,
                    "duration_seconds": duration,
                    "errors": errors,
                    "logs": logs,
                }
            )

            # Persist sync operation to database
            try:
                operation_id = self.sync.persist(sync_operation)
                logger.debug(f"Saved sync operation with ID: {operation_id}")
            except Exception as e:
                logger.error(f"Failed to persist sync operation: {e}")

            result = SyncResult(
                success=len(errors) == 0,
                accounts_processed=accounts_processed,
                transactions_added=transactions_added,
                transactions_updated=transactions_updated,
                balances_updated=balances_updated,
                duration_seconds=duration,
                errors=errors,
                started_at=start_time,
                completed_at=end_time,
            )

            logger.info(
                f"Sync completed: {accounts_processed} accounts, {transactions_added} new transactions"
            )
            logs.append(
                f"Sync completed: {accounts_processed} accounts, {transactions_added} new transactions"
            )
            return result

        except Exception as e:
            error_msg = f"Sync failed: {str(e)}"
            errors.append(error_msg)
            logs.append(error_msg)
            logger.error(error_msg)

            # Save failed sync operation
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            sync_operation.update(
                {
                    "completed_at": end_time.isoformat(),
                    "success": False,
                    "accounts_processed": accounts_processed,
                    "transactions_added": transactions_added,
                    "transactions_updated": transactions_updated,
                    "balances_updated": balances_updated,
                    "duration_seconds": duration,
                    "errors": errors,
                    "logs": logs,
                }
            )

            try:
                operation_id = self.sync.persist(sync_operation)
                logger.debug(f"Saved failed sync operation with ID: {operation_id}")
            except Exception as persist_error:
                logger.error(
                    f"Failed to persist failed sync operation: {persist_error}"
                )

            raise
        finally:
            self._sync_status.is_running = False

    async def _check_session_expiry(self, sessions: List[dict]) -> None:
        """Check sessions for expiry and send notifications.

        Args:
            sessions: List of session dictionaries to check
        """
        now = datetime.now()
        for session in sessions:
            session_id = session.get("session_id", "unknown")
            aspsp_name = session.get("aspsp_name", "unknown")
            valid_until_str = session.get("valid_until")

            if not valid_until_str:
                continue

            try:
                valid_until = datetime.fromisoformat(valid_until_str)
                if valid_until < now:
                    logger.warning(f"Session {session_id} for {aspsp_name} has expired")
                    await self.notifications.send_expiry_notification(
                        {
                            "bank": aspsp_name,
                            "session_id": session_id,
                            "status": "expired",
                            "days_left": EXPIRED_DAYS_LEFT,
                        }
                    )
            except (ValueError, TypeError):
                continue

    async def sync_specific_accounts(
        self,
        account_ids: List[str],
        full_sync: bool = False,
        trigger_type: str = "manual",
    ) -> SyncResult:
        """Sync specific accounts"""
        if self._sync_status.is_running:
            raise Exception("Sync is already running")

        self._sync_status.is_running = True

        try:
            # For now, delegate to sync_all_accounts
            result = await self.sync_all_accounts(
                full_sync=full_sync, trigger_type=trigger_type
            )
            return result

        finally:
            self._sync_status.is_running = False
