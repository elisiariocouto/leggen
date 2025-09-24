import click
import requests

from leggen.utils.text import info


def escape_markdown(text: str) -> str:
    return (
        str(text)
        .replace("_", "\\_")
        .replace("*", "\\*")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("~", "\\~")
        .replace("`", "\\`")
        .replace(">", "\\>")
        .replace("#", "\\#")
        .replace("+", "\\+")
        .replace("-", "\\-")
        .replace("=", "\\=")
        .replace("|", "\\|")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace(".", "\\.")
        .replace("!", "\\!")
    )


def send_expire_notification(ctx: click.Context, notification: dict):
    token = ctx.obj["notifications"]["telegram"]["token"]
    chat_id = ctx.obj["notifications"]["telegram"]["chat_id"]
    bot_url = f"https://api.telegram.org/bot{token}/sendMessage"
    info("Sending expiration notification to Telegram")
    message = "*💲 [Leggen](https://github.com/elisiariocouto/leggen)*\n"
    message += escape_markdown(
        f"Your account {notification['bank']} ({notification['requisition_id']}) is in {notification['status']} status. Days left: {notification['days_left']}\n"
    )

    res = requests.post(
        bot_url,
        json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "MarkdownV2",
        },
    )

    try:
        res.raise_for_status()
    except Exception as e:
        raise Exception(f"Telegram notification failed: {e}\n{res.text}") from e


def send_transaction_message(ctx: click.Context, transactions: list):
    token = ctx.obj["notifications"]["telegram"]["token"]
    chat_id = ctx.obj["notifications"]["telegram"]["chat_id"]
    bot_url = f"https://api.telegram.org/bot{token}/sendMessage"
    info(f"Got {len(transactions)} new transactions, sending message to Telegram")
    message = "*💲 [Leggen](https://github.com/elisiariocouto/leggen)*\n"
    message += f"{len(transactions)} new transaction matches\n\n"

    for transaction in transactions:
        message += f"*Name*: {escape_markdown(transaction['name'])}\n"
        message += f"*Value*: {escape_markdown(transaction['value'])}{escape_markdown(transaction['currency'])}\n"
        message += f"*Date*: {escape_markdown(transaction['date'])}\n\n"

    res = requests.post(
        bot_url,
        json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "MarkdownV2",
        },
    )

    try:
        res.raise_for_status()
    except Exception as e:
        raise Exception(f"Telegram notification failed: {e}\n{res.text}") from e


def send_sync_failure_notification(ctx: click.Context, notification: dict):
    token = ctx.obj["notifications"]["telegram"]["token"]
    chat_id = ctx.obj["notifications"]["telegram"]["chat_id"]
    bot_url = f"https://api.telegram.org/bot{token}/sendMessage"
    info("Sending sync failure notification to Telegram")

    message = "*🚨 [Leggen](https://github.com/elisiariocouto/leggen)*\n"
    message += "*Sync Failed*\n\n"
    message += escape_markdown(f"Error: {notification['error']}\n")

    if notification.get("type") == "sync_final_failure":
        message += escape_markdown(
            f"❌ Final failure after {notification['retry_count']} attempts\n"
        )
    else:
        message += escape_markdown(
            f"🔄 Attempt {notification['retry_count']}/{notification['max_retries']}\n"
        )
        message += escape_markdown("Will retry automatically...\n")

    res = requests.post(
        bot_url,
        json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "MarkdownV2",
        },
    )

    try:
        res.raise_for_status()
    except Exception as e:
        raise Exception(f"Telegram notification failed: {e}\n{res.text}") from e
