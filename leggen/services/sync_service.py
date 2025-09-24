from datetime import datetime
from typing import List

from loguru import logger

from leggen.api.models.sync import SyncResult, SyncStatus
from leggen.services.database_service import DatabaseService
from leggen.services.gocardless_service import GoCardlessService
from leggen.services.notification_service import NotificationService


class SyncService:
    def __init__(self):
        self.gocardless = GoCardlessService()
        self.database = DatabaseService()
        self.notifications = NotificationService()
        self._sync_status = SyncStatus(is_running=False)
        self._institution_logos = {}  # Cache for institution logos

    async def get_sync_status(self) -> SyncStatus:
        """Get current sync status"""
        return self._sync_status

    async def sync_all_accounts(
        self, force: bool = False, trigger_type: str = "manual"
    ) -> SyncResult:
        """Sync all connected accounts"""
        if self._sync_status.is_running and not force:
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

            # Get all requisitions and accounts
            requisitions = await self.gocardless.get_requisitions()
            all_accounts = set()

            for req in requisitions.get("results", []):
                all_accounts.update(req.get("accounts", []))

            self._sync_status.total_accounts = len(all_accounts)
            logs.append(f"Found {len(all_accounts)} accounts to sync")

            # Process each account
            for account_id in all_accounts:
                try:
                    # Get account details
                    account_details = await self.gocardless.get_account_details(
                        account_id
                    )

                    # Get balances to extract currency information
                    balances = await self.gocardless.get_account_balances(account_id)

                    # Enrich account details with currency and institution logo
                    if account_details and balances:
                        enriched_account_details = account_details.copy()

                        # Extract currency from first balance
                        balances_list = balances.get("balances", [])
                        if balances_list:
                            first_balance = balances_list[0]
                            balance_amount = first_balance.get("balanceAmount", {})
                            currency = balance_amount.get("currency")
                            if currency:
                                enriched_account_details["currency"] = currency

                        # Get institution details to fetch logo
                        institution_id = enriched_account_details.get("institution_id")
                        if institution_id:
                            try:
                                institution_details = (
                                    await self.gocardless.get_institution_details(
                                        institution_id
                                    )
                                )
                                enriched_account_details["logo"] = (
                                    institution_details.get("logo", "")
                                )
                                logger.info(
                                    f"Fetched logo for institution {institution_id}: {enriched_account_details.get('logo', 'No logo')}"
                                )
                            except Exception as e:
                                logger.warning(
                                    f"Failed to fetch institution details for {institution_id}: {e}"
                                )

                        # Persist enriched account details to database
                        await self.database.persist_account_details(
                            enriched_account_details
                        )

                        # Merge account details into balances data for proper persistence
                        balances_with_account_info = balances.copy()
                        balances_with_account_info["institution_id"] = (
                            enriched_account_details.get("institution_id")
                        )
                        balances_with_account_info["iban"] = (
                            enriched_account_details.get("iban")
                        )
                        balances_with_account_info["account_status"] = (
                            enriched_account_details.get("status")
                        )
                        await self.database.persist_balance(
                            account_id, balances_with_account_info
                        )
                        balances_updated += len(balances.get("balances", []))
                    elif account_details:
                        # Fallback: persist account details without currency if balances failed
                        await self.database.persist_account_details(account_details)

                    # Get and save transactions
                    transactions = await self.gocardless.get_account_transactions(
                        account_id
                    )
                    if transactions:
                        processed_transactions = self.database.process_transactions(
                            account_id, account_details, transactions
                        )
                        new_transactions = await self.database.persist_transactions(
                            account_id, processed_transactions
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
                operation_id = await self.database.persist_sync_operation(
                    sync_operation
                )
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
                operation_id = await self.database.persist_sync_operation(
                    sync_operation
                )
                logger.debug(f"Saved failed sync operation with ID: {operation_id}")
            except Exception as persist_error:
                logger.error(
                    f"Failed to persist failed sync operation: {persist_error}"
                )

            raise
        finally:
            self._sync_status.is_running = False

    async def sync_specific_accounts(
        self, account_ids: List[str], force: bool = False, trigger_type: str = "manual"
    ) -> SyncResult:
        """Sync specific accounts"""
        if self._sync_status.is_running and not force:
            raise Exception("Sync is already running")

        self._sync_status.is_running = True

        try:
            # For now, delegate to sync_all_accounts but with specific filtering
            # This could be optimized later to only process specified accounts
            result = await self.sync_all_accounts(
                force=force, trigger_type=trigger_type
            )

            # Filter results to only specified accounts if needed
            # For simplicity, we'll return the full result for now
            return result

        finally:
            self._sync_status.is_running = False
