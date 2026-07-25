from typing import Any, Dict, List

from loguru import logger

from leggen.notifications import discord, telegram
from leggen.utils.config import config


class NotificationService:
    # Config is read live via properties (not cached at construction) so
    # settings changes apply without a server restart.
    @property
    def notifications_config(self) -> Dict[str, Any]:
        return config.notifications_config

    @property
    def filters_config(self) -> Dict[str, Any]:
        return config.filters_config

    async def send_transaction_notifications(
        self, transactions: List[Dict[str, Any]]
    ) -> None:
        """Send notifications for new transactions that match filters."""
        if not self.filters_config:
            logger.info("No notification filters configured, skipping notifications")
            return

        matching_transactions = self._filter_transactions(transactions)

        if not matching_transactions:
            logger.info("No transactions matched notification filters")
            return

        if self._is_discord_enabled():
            await self._send_discord_notifications(matching_transactions)

        if self._is_telegram_enabled():
            await self._send_telegram_notifications(matching_transactions)

    async def send_test_notification(self, service: str) -> bool:
        """Send a test notification."""
        try:
            if service == "discord" and self._is_discord_enabled():
                await self._send_discord_test()
                return True
            elif service == "telegram" and self._is_telegram_enabled():
                await self._send_telegram_test()
                return True
            else:
                logger.error(
                    f"Notification service '{service}' not enabled or not found"
                )
                return False
        except Exception as e:
            logger.error(f"Failed to send test notification to {service}: {e}")
            return False

    async def send_expiry_notification(self, notification_data: Dict[str, Any]) -> None:
        """Send notification about account expiry."""
        try:
            if self._is_discord_enabled():
                webhook_url = self._get_discord_webhook()
                await discord.send_expire_notification(webhook_url, notification_data)
                logger.info(f"Sent Discord expiry notification: {notification_data}")
        except Exception as e:
            logger.error(f"Failed to send Discord expiry notification: {e}")

        try:
            if self._is_telegram_enabled():
                token, chat_id = self._get_telegram_credentials()
                await telegram.send_expire_notification(
                    token, chat_id, notification_data
                )
                logger.info(f"Sent Telegram expiry notification: {notification_data}")
        except Exception as e:
            logger.error(f"Failed to send Telegram expiry notification: {e}")

    async def send_sync_failure_notification(
        self, notification_data: Dict[str, Any]
    ) -> None:
        """Send notification about sync failure."""
        try:
            if self._is_discord_enabled():
                webhook_url = self._get_discord_webhook()
                await discord.send_sync_failure_notification(
                    webhook_url, notification_data
                )
                logger.info(
                    f"Sent Discord sync failure notification: {notification_data}"
                )
        except Exception as e:
            logger.error(f"Failed to send Discord sync failure notification: {e}")

        try:
            if self._is_telegram_enabled():
                token, chat_id = self._get_telegram_credentials()
                await telegram.send_sync_failure_notification(
                    token, chat_id, notification_data
                )
                logger.info(
                    f"Sent Telegram sync failure notification: {notification_data}"
                )
        except Exception as e:
            logger.error(f"Failed to send Telegram sync failure notification: {e}")

    def _filter_transactions(
        self, transactions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter transactions based on notification criteria."""
        matching = []
        filters_case_insensitive = self.filters_config.get("case_insensitive", [])
        filters_case_sensitive = self.filters_config.get("case_sensitive", [])

        for transaction in transactions:
            description = transaction.get("description", "")
            description_lower = description.lower()

            matches = any(
                filter_value.lower() in description_lower
                for filter_value in filters_case_insensitive
            ) or any(
                filter_value in description for filter_value in filters_case_sensitive
            )

            if matches:
                matching.append(
                    {
                        "name": transaction["description"],
                        "value": transaction["transactionValue"],
                        "currency": transaction["transactionCurrency"],
                        "date": transaction["transactionDate"],
                    }
                )

        return matching

    def _is_discord_enabled(self) -> bool:
        discord_config = self.notifications_config.get("discord", {})
        return bool(
            discord_config.get("webhook") and discord_config.get("enabled", True)
        )

    def _is_telegram_enabled(self) -> bool:
        telegram_config = self.notifications_config.get("telegram", {})
        return bool(
            telegram_config.get("token")
            and telegram_config.get("chat_id")
            and telegram_config.get("enabled", True)
        )

    def _get_discord_webhook(self) -> str:
        return self.notifications_config.get("discord", {}).get("webhook", "")

    def _get_telegram_credentials(self) -> tuple[str, str]:
        telegram_config = self.notifications_config.get("telegram", {})
        return telegram_config.get("token", ""), telegram_config.get("chat_id", "")

    async def _send_discord_notifications(
        self, transactions: List[Dict[str, Any]]
    ) -> None:
        try:
            webhook_url = self._get_discord_webhook()
            await discord.send_transactions_message(webhook_url, transactions)
            logger.info(
                f"Sent {len(transactions)} transaction notifications to Discord"
            )
        except Exception as e:
            # Never re-raise: a notification failure must not mark an
            # otherwise successful sync as failed.
            logger.error(f"Failed to send Discord transaction notifications: {e}")

    async def _send_telegram_notifications(
        self, transactions: List[Dict[str, Any]]
    ) -> None:
        try:
            token, chat_id = self._get_telegram_credentials()
            await telegram.send_transaction_message(token, chat_id, transactions)
            logger.info(
                f"Sent {len(transactions)} transaction notifications to Telegram"
            )
        except Exception as e:
            # Never re-raise: a notification failure must not mark an
            # otherwise successful sync as failed.
            logger.error(f"Failed to send Telegram transaction notifications: {e}")

    async def _send_discord_test(self) -> None:
        try:
            await discord.send_test_notification(self._get_discord_webhook())
            logger.info("Discord test notification sent")
        except Exception as e:
            logger.error(f"Failed to send Discord test notification: {e}")
            raise

    async def _send_telegram_test(self) -> None:
        try:
            token, chat_id = self._get_telegram_credentials()
            await telegram.send_test_notification(token, chat_id)
            logger.info("Telegram test notification sent")
        except Exception as e:
            logger.error(f"Failed to send Telegram test notification: {e}")
            raise
