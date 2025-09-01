from typing import List, Dict, Any

from loguru import logger

from leggend.config import config


class NotificationService:
    def __init__(self):
        self.notifications_config = config.notifications_config
        self.filters_config = config.filters_config

    async def send_transaction_notifications(self, transactions: List[Dict[str, Any]]) -> None:
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
                logger.error(f"Notification service '{service}' not enabled or not found")
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

    def _filter_transactions(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter transactions based on notification criteria"""
        matching = []
        filters_case_insensitive = self.filters_config.get("case-insensitive", {})
        
        for transaction in transactions:
            description = transaction.get("description", "").lower()
            
            # Check case-insensitive filters
            for filter_name, filter_value in filters_case_insensitive.items():
                if filter_value.lower() in description:
                    matching.append({
                        "name": transaction["description"],
                        "value": transaction["transactionValue"], 
                        "currency": transaction["transactionCurrency"],
                        "date": transaction["transactionDate"],
                    })
                    break
        
        return matching

    def _is_discord_enabled(self) -> bool:
        """Check if Discord notifications are enabled"""
        discord_config = self.notifications_config.get("discord", {})
        return bool(discord_config.get("webhook") and discord_config.get("enabled", True))

    def _is_telegram_enabled(self) -> bool:
        """Check if Telegram notifications are enabled"""
        telegram_config = self.notifications_config.get("telegram", {})
        return bool(
            telegram_config.get("token") and 
            telegram_config.get("chat_id") and 
            telegram_config.get("enabled", True)
        )

    async def _send_discord_notifications(self, transactions: List[Dict[str, Any]]) -> None:
        """Send Discord notifications - placeholder implementation"""
        # Would import and use leggen.notifications.discord
        logger.info(f"Sending {len(transactions)} transaction notifications to Discord")

    async def _send_telegram_notifications(self, transactions: List[Dict[str, Any]]) -> None:
        """Send Telegram notifications - placeholder implementation"""
        # Would import and use leggen.notifications.telegram
        logger.info(f"Sending {len(transactions)} transaction notifications to Telegram")

    async def _send_discord_test(self, message: str) -> None:
        """Send Discord test notification"""
        logger.info(f"Sending Discord test: {message}")

    async def _send_telegram_test(self, message: str) -> None:
        """Send Telegram test notification"""
        logger.info(f"Sending Telegram test: {message}")

    async def _send_discord_expiry(self, notification_data: Dict[str, Any]) -> None:
        """Send Discord expiry notification"""
        logger.info(f"Sending Discord expiry notification: {notification_data}")

    async def _send_telegram_expiry(self, notification_data: Dict[str, Any]) -> None:
        """Send Telegram expiry notification"""
        logger.info(f"Sending Telegram expiry notification: {notification_data}")