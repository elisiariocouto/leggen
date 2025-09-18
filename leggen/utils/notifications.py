import click

import leggen.notifications.discord as discord
import leggen.notifications.telegram as telegram
from leggen.utils.text import error, info, warning


def send_expire_notification(ctx: click.Context, notification: dict):
    discord_enabled = ctx.obj.get("notifications", {}).get("discord", False)
    telegram_enabled = ctx.obj.get("notifications", {}).get("telegram", False)

    if not discord_enabled and not telegram_enabled:
        warning("No notification engine is enabled, skipping notifications")
        error(
            f"Your account {notification['bank']} ({notification['requisition_id']}) is in {notification['status']} status. Days left: {notification['days_left']}"
        )

    if discord_enabled:
        info("Sending expiration notification to Discord")
        discord.send_expire_notification(ctx, notification)

    if telegram_enabled:
        info("Sending expiration notification to Telegram")
        telegram.send_expire_notification(ctx, notification)


def send_notification(ctx: click.Context, transactions: list):
    if ctx.obj.get("filters") is None:
        warning("No filters are enabled, skipping notifications")
        return

    filters_case_insensitive = ctx.obj.get("filters", {}).get("case_insensitive", {})

    # Add transaction to the list of transactions to be sent as a notification
    notification_transactions = []
    for transaction in transactions:
        for _, v in filters_case_insensitive.items():
            if v.lower() in transaction["description"].lower():
                notification_transactions.append(
                    {
                        "name": transaction["description"],
                        "value": transaction["transactionValue"],
                        "currency": transaction["transactionCurrency"],
                        "date": transaction["transactionDate"],
                    }
                )

    if len(notification_transactions) == 0:
        warning("No transactions matched the filters, skipping notifications")
        return

    discord_enabled = ctx.obj.get("notifications", {}).get("discord", False)
    telegram_enabled = ctx.obj.get("notifications", {}).get("telegram", False)

    if not discord_enabled and not telegram_enabled:
        warning("No notification engine is enabled, skipping notifications")
        return

    if discord_enabled:
        info(f"Sending {len(notification_transactions)} transactions to Discord")
        discord.send_transactions_message(ctx, notification_transactions)

    if telegram_enabled:
        info(f"Sending {len(notification_transactions)} transactions to Telegram")
        telegram.send_transaction_message(ctx, notification_transactions)
