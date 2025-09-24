from typing import Any, Dict, List

from loguru import logger

from leggen.utils.config import config


class NotificationService:
    def __init__(self):
        self.notifications_config = config.notifications_config
        self.filters_config = config.filters_config

    async def send_transaction_notifications(
        self, transactions: List[Dict[str, Any]]
    ) -> None:
        """Send notifications for new transactions that match filters"""
        if not self.filters_config:
            logger.info("No notification filters configured, skipping notifications")
            return

        # Filter transactions that match notification criteria
        matching_transactions = self._filter_transactions(transactions)

        if not matching_transactions:
            logger.info("No transactions matched notification filters")
            return

        # Send to enabled notification services
        if self._is_discord_enabled():
            await self._send_discord_notifications(matching_transactions)

        if self._is_telegram_enabled():
            await self._send_telegram_notifications(matching_transactions)

    async def send_test_notification(self, service: str, message: str) -> bool:
        """Send a test notification"""
        try:
            if service == "discord" and self._is_discord_enabled():
                await self._send_discord_test(message)
                return True
            elif service == "telegram" and self._is_telegram_enabled():
                await self._send_telegram_test(message)
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
        """Send notification about account expiry"""
        if self._is_discord_enabled():
            await self._send_discord_expiry(notification_data)

        if self._is_telegram_enabled():
            await self._send_telegram_expiry(notification_data)

    def _filter_transactions(
        self, transactions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter transactions based on notification criteria"""
        matching = []
        filters_case_insensitive = self.filters_config.get("case_insensitive", [])
        filters_case_sensitive = self.filters_config.get("case_sensitive", [])

        for transaction in transactions:
            description = transaction.get("description", "")
            description_lower = description.lower()

            # Check case-insensitive filters
            for filter_value in filters_case_insensitive:
                if filter_value.lower() in description_lower:
                    matching.append(
                        {
                            "name": transaction["description"],
                            "value": transaction["transactionValue"],
                            "currency": transaction["transactionCurrency"],
                            "date": transaction["transactionDate"],
                        }
                    )
                    break

            # Check case-sensitive filters
            for filter_value in filters_case_sensitive:
                if filter_value in description:
                    matching.append(
                        {
                            "name": transaction["description"],
                            "value": transaction["transactionValue"],
                            "currency": transaction["transactionCurrency"],
                            "date": transaction["transactionDate"],
                        }
                    )
                    break

        return matching

    def _is_discord_enabled(self) -> bool:
        """Check if Discord notifications are enabled"""
        discord_config = self.notifications_config.get("discord", {})
        return bool(
            discord_config.get("webhook") and discord_config.get("enabled", True)
        )

    def _is_telegram_enabled(self) -> bool:
        """Check if Telegram notifications are enabled"""
        telegram_config = self.notifications_config.get("telegram", {})
        return bool(
            telegram_config.get("token")
            and telegram_config.get("chat_id")
            and telegram_config.get("enabled", True)
        )

    async def _send_discord_notifications(
        self, transactions: List[Dict[str, Any]]
    ) -> None:
        """Send Discord notifications for transactions"""
        try:
            import click

            from leggen.notifications.discord import send_transactions_message

            # Create a mock context with the webhook
            ctx = click.Context(click.Command("notifications"))
            ctx.obj = {
                "notifications": {
                    "discord": {
                        "webhook": self.notifications_config.get("discord", {}).get(
                            "webhook"
                        )
                    }
                }
            }

            # Send transaction notifications using the actual implementation
            send_transactions_message(ctx, transactions)
            logger.info(
                f"Sent {len(transactions)} transaction notifications to Discord"
            )
        except Exception as e:
            logger.error(f"Failed to send Discord transaction notifications: {e}")
            raise

    async def _send_telegram_notifications(
        self, transactions: List[Dict[str, Any]]
    ) -> None:
        """Send Telegram notifications for transactions"""
        try:
            import click

            from leggen.notifications.telegram import send_transaction_message

            # Create a mock context with the telegram config
            ctx = click.Context(click.Command("notifications"))
            telegram_config = self.notifications_config.get("telegram", {})
            ctx.obj = {
                "notifications": {
                    "telegram": {
                        "token": telegram_config.get("token"),
                        "chat_id": telegram_config.get("chat_id"),
                    }
                }
            }

            # Send transaction notifications using the actual implementation
            send_transaction_message(ctx, transactions)
            logger.info(
                f"Sent {len(transactions)} transaction notifications to Telegram"
            )
        except Exception as e:
            logger.error(f"Failed to send Telegram transaction notifications: {e}")
            raise

    async def _send_discord_test(self, message: str) -> None:
        """Send Discord test notification"""
        try:
            import click

            from leggen.notifications.discord import send_expire_notification

            # Create a mock context with the webhook
            ctx = click.Context(click.Command("test"))
            ctx.obj = {
                "notifications": {
                    "discord": {
                        "webhook": self.notifications_config.get("discord", {}).get(
                            "webhook"
                        )
                    }
                }
            }

            # Send test notification using the actual implementation
            test_notification = {
                "bank": "Test",
                "requisition_id": "test-123",
                "status": "active",
                "days_left": 30,
            }
            send_expire_notification(ctx, test_notification)
            logger.info(f"Discord test notification sent: {message}")
        except Exception as e:
            logger.error(f"Failed to send Discord test notification: {e}")
            raise

    async def _send_telegram_test(self, message: str) -> None:
        """Send Telegram test notification"""
        try:
            import click

            from leggen.notifications.telegram import send_expire_notification

            # Create a mock context with the telegram config
            ctx = click.Context(click.Command("test"))
            telegram_config = self.notifications_config.get("telegram", {})
            ctx.obj = {
                "notifications": {
                    "telegram": {
                        "token": telegram_config.get("token"),
                        "chat_id": telegram_config.get("chat_id"),
                    }
                }
            }

            # Send test notification using the actual implementation
            test_notification = {
                "bank": "Test",
                "requisition_id": "test-123",
                "status": "active",
                "days_left": 30,
            }
            send_expire_notification(ctx, test_notification)
            logger.info(f"Telegram test notification sent: {message}")
        except Exception as e:
            logger.error(f"Failed to send Telegram test notification: {e}")
            raise

    async def _send_discord_expiry(self, notification_data: Dict[str, Any]) -> None:
        """Send Discord expiry notification"""
        try:
            import click

            from leggen.notifications.discord import send_expire_notification

            # Create a mock context with the webhook
            ctx = click.Context(click.Command("expiry"))
            ctx.obj = {
                "notifications": {
                    "discord": {
                        "webhook": self.notifications_config.get("discord", {}).get(
                            "webhook"
                        )
                    }
                }
            }

            # Send expiry notification using the actual implementation
            send_expire_notification(ctx, notification_data)
            logger.info(f"Sent Discord expiry notification: {notification_data}")
        except Exception as e:
            logger.error(f"Failed to send Discord expiry notification: {e}")
            raise

    async def _send_telegram_expiry(self, notification_data: Dict[str, Any]) -> None:
        """Send Telegram expiry notification"""
        try:
            import click

            from leggen.notifications.telegram import send_expire_notification

            # Create a mock context with the telegram config
            ctx = click.Context(click.Command("expiry"))
            telegram_config = self.notifications_config.get("telegram", {})
            ctx.obj = {
                "notifications": {
                    "telegram": {
                        "token": telegram_config.get("token"),
                        "chat_id": telegram_config.get("chat_id"),
                    }
                }
            }

            # Send expiry notification using the actual implementation
            send_expire_notification(ctx, notification_data)
            logger.info(f"Sent Telegram expiry notification: {notification_data}")
        except Exception as e:
            logger.error(f"Failed to send Telegram expiry notification: {e}")
            raise

    async def send_sync_failure_notification(
        self, notification_data: Dict[str, Any]
    ) -> None:
        """Send notification about sync failure"""
        if self._is_discord_enabled():
            await self._send_discord_sync_failure(notification_data)

        if self._is_telegram_enabled():
            await self._send_telegram_sync_failure(notification_data)

    async def _send_discord_sync_failure(
        self, notification_data: Dict[str, Any]
    ) -> None:
        """Send Discord sync failure notification"""
        try:
            import click

            from leggen.notifications.discord import send_sync_failure_notification

            # Create a mock context with the webhook
            ctx = click.Context(click.Command("sync_failure"))
            ctx.obj = {
                "notifications": {
                    "discord": {
                        "webhook": self.notifications_config.get("discord", {}).get(
                            "webhook"
                        )
                    }
                }
            }

            # Send sync failure notification using the actual implementation
            send_sync_failure_notification(ctx, notification_data)
            logger.info(f"Sent Discord sync failure notification: {notification_data}")
        except Exception as e:
            logger.error(f"Failed to send Discord sync failure notification: {e}")
            raise

    async def _send_telegram_sync_failure(
        self, notification_data: Dict[str, Any]
    ) -> None:
        """Send Telegram sync failure notification"""
        try:
            import click

            from leggen.notifications.telegram import send_sync_failure_notification

            # Create a mock context with the telegram config
            ctx = click.Context(click.Command("sync_failure"))
            telegram_config = self.notifications_config.get("telegram", {})
            ctx.obj = {
                "notifications": {
                    "telegram": {
                        "token": telegram_config.get("token"),
                        "chat_id": telegram_config.get("chat_id"),
                    }
                }
            }

            # Send sync failure notification using the actual implementation
            send_sync_failure_notification(ctx, notification_data)
            logger.info(f"Sent Telegram sync failure notification: {notification_data}")
        except Exception as e:
            logger.error(f"Failed to send Telegram sync failure notification: {e}")
            raise
