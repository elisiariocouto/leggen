from typing import Any, Dict, List

import click

from leggen.services.push_service import PushService
from leggen.utils.text import info


def send_expire_notification(ctx: click.Context, notification: dict):
    """Send expiration notification via push notification"""
    info("Sending expiration notification via push")
    push_service = PushService()

    if not push_service.is_push_enabled():
        info("Push notifications not enabled, skipping")
        return

    push_service.send_expiry_notification(
        notification["bank"],
        notification["requisition_id"],
        notification["status"],
        notification["days_left"],
    )


def send_transaction_message(ctx: click.Context, transactions: List[Dict[str, Any]]):
    """Send transaction notification via push notification"""
    info(f"Got {len(transactions)} new transactions, sending push notification")
    push_service = PushService()

    if not push_service.is_push_enabled():
        info("Push notifications not enabled, skipping")
        return

    # Create a summary
    total_value = sum(float(t.get("value", 0)) for t in transactions)
    currencies = {t.get("currency", "EUR") for t in transactions}
    currency = list(currencies)[0] if len(currencies) == 1 else "mixed"

    push_service.send_transaction_notification(len(transactions), total_value, currency)


def send_test_notification(ctx: click.Context, message: str):
    """Send test push notification"""
    info("Sending test push notification")
    push_service = PushService()

    if not push_service.is_push_enabled():
        info("Push notifications not enabled, skipping")
        return

    push_service.send_test_notification(message)
