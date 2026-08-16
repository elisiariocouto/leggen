from datetime import UTC, datetime
from typing import Any

import httpx

from leggen.utils.text import info

_AUTHOR = {"name": "Leggen", "url": "https://github.com/elisiariocouto/leggen"}
_INFO_COLOR = 0x03B2F8
_WARNING_COLOR = 0xFFAA00


async def _post_embed(webhook_url: str, embed: dict[str, Any]) -> None:
    """Post a single embed to a Discord webhook."""
    embed.setdefault("author", _AUTHOR)
    embed.setdefault("timestamp", datetime.now(UTC).isoformat())

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(webhook_url, json={"embeds": [embed]})
        if response.status_code >= 400:
            raise Exception(
                f"Discord notification failed: {response.status_code}\n{response.text}"
            )


async def send_expire_notification(webhook_url: str, notification: dict):
    info("Sending expiration notification to Discord")
    await _post_embed(
        webhook_url,
        {
            "description": (
                f"Your account {notification['bank']} ({notification['session_id']}) "
                f"is in {notification['status']} status. "
                f"Days left: {notification['days_left']}"
            ),
            "color": _INFO_COLOR,
            "footer": {"text": "Expiration notice"},
        },
    )


async def send_test_notification(webhook_url: str):
    info("Sending test notification to Discord")
    await _post_embed(
        webhook_url,
        {
            "title": "🔔 Test Notification",
            "description": "Leggen notifications are configured correctly.",
            "color": _INFO_COLOR,
            "footer": {"text": "Test notification"},
        },
    )


async def send_transactions_message(webhook_url: str, transactions: list):
    info(f"Got {len(transactions)} new transactions, sending message to Discord")
    await _post_embed(
        webhook_url,
        {
            "description": f"{len(transactions)} new transaction matches",
            "color": _INFO_COLOR,
            "footer": {"text": "Transaction filters"},
            "fields": [
                {
                    "name": str(transaction["name"])[:256],
                    "value": (
                        f"{transaction['value']}{transaction['currency']} "
                        f"({transaction['date']})"
                    ),
                    "inline": False,
                }
                for transaction in transactions[:25]  # Discord caps fields at 25
            ],
        },
    )


async def send_sync_failure_notification(webhook_url: str, notification: dict):
    info("Sending sync failure notification to Discord")

    description = "Account sync failed"
    if notification.get("account_id"):
        description = f"Account {notification['account_id']} sync failed"

    await _post_embed(
        webhook_url,
        {
            "title": "⚠️ Sync Failure",
            "description": description,
            "color": _WARNING_COLOR,
            "footer": {"text": "Sync failure notification"},
            "fields": [
                {
                    "name": "Error",
                    "value": notification["error"][:1024],  # Discord field limit
                    "inline": False,
                }
            ],
        },
    )
