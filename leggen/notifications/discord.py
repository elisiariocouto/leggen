import click
from discord_webhook import DiscordEmbed, DiscordWebhook

from leggen.utils.text import info


def send_expire_notification(ctx: click.Context, notification: dict):
    info("Sending expiration notification to Discord")
    webhook = DiscordWebhook(url=ctx.obj["notifications"]["discord"]["webhook"])

    embed = DiscordEmbed(
        title="",
        description=f"Your account {notification['bank']} ({notification['requisition_id']}) is in {notification['status']} status. Days left: {notification['days_left']}",
        color="03b2f8",
    )
    embed.set_author(
        name="Leggen",
        url="https://github.com/elisiariocouto/leggen",
    )
    embed.set_footer(text="Expiration notice")
    embed.set_timestamp()

    webhook.add_embed(embed)
    response = webhook.execute()
    try:
        response.raise_for_status()
    except Exception as e:
        raise Exception(f"Discord notification failed: {e}\n{response.text}") from e


def send_transactions_message(ctx: click.Context, transactions: list):
    info(f"Got {len(transactions)} new transactions, sending message to Discord")
    webhook = DiscordWebhook(url=ctx.obj["notifications"]["discord"]["webhook"])

    embed = DiscordEmbed(
        title="",
        description=f"{len(transactions)} new transaction matches",
        color="03b2f8",
    )
    embed.set_author(
        name="Leggen",
        url="https://github.com/elisiariocouto/leggen",
    )
    embed.set_footer(text="Case-insensitive filters")
    embed.set_timestamp()
    for transaction in transactions:
        embed.add_embed_field(
            name=transaction["name"],
            value=f"{transaction['value']}{transaction['currency']} ({transaction['date']})",
        )

    webhook.add_embed(embed)
    response = webhook.execute()
    try:
        response.raise_for_status()
    except Exception as e:
        raise Exception(f"Discord notification failed: {e}\n{response.text}") from e


def send_sync_failure_notification(ctx: click.Context, notification: dict):
    info("Sending sync failure notification to Discord")
    webhook = DiscordWebhook(url=ctx.obj["notifications"]["discord"]["webhook"])

    # Determine color and title based on failure type
    if notification.get("type") == "sync_final_failure":
        color = "ff0000"  # Red for final failure
        title = "🚨 Sync Final Failure"
        description = (
            f"Sync failed permanently after {notification['retry_count']} attempts"
        )
    else:
        color = "ffaa00"  # Orange for retry
        title = "⚠️ Sync Failure"
        description = f"Sync failed (attempt {notification['retry_count']}/{notification['max_retries']}). Will retry automatically..."

    embed = DiscordEmbed(
        title=title,
        description=description,
        color=color,
    )
    embed.set_author(
        name="Leggen",
        url="https://github.com/elisiariocouto/leggen",
    )
    embed.add_embed_field(
        name="Error",
        value=notification["error"][:1024],  # Discord has field value limits
        inline=False,
    )
    embed.set_footer(text="Sync failure notification")
    embed.set_timestamp()

    webhook.add_embed(embed)
    response = webhook.execute()
    try:
        response.raise_for_status()
    except Exception as e:
        raise Exception(f"Discord notification failed: {e}\n{response.text}") from e
