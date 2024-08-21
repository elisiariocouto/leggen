import click
import requests

from leggen.utils.text import info


def escape_markdown(text: str) -> str:
    return (
        str(text)
        .replace("-", "\\-")
        .replace("#", "\\#")
        .replace(".", "\\.")
        .replace("$", "\\$")
        .replace("+", "\\+")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )


def send_expire_notification(ctx: click.Context, notification: dict):
    token = ctx.obj["notifications"]["telegram"]["api-key"]
    chat_id = ctx.obj["notifications"]["telegram"]["chat-id"]
    bot_url = f"https://api.telegram.org/bot{token}/sendMessage"
    info("Sending expiration notification to Telegram")
    message = "*💲 [Leggen](https://github.com/elisiariocouto/leggen)*\n"
    message += f"Your account {notification['bank']} ({notification['requisition_id']}) is in {notification['status']} status. Days left: {notification['days_left']}\n"

    res = requests.post(
        bot_url,
        json={
            "chat_id": chat_id,
            "text": escape_markdown(message),
            "parse_mode": "MarkdownV2",
        },
    )

    try:
        res.raise_for_status()
    except Exception as e:
        raise Exception(f"Telegram notification failed: {e}\n{res.text}") from e


def send_transaction_message(ctx: click.Context, transactions: list):
    token = ctx.obj["notifications"]["telegram"]["api-key"]
    chat_id = ctx.obj["notifications"]["telegram"]["chat-id"]
    bot_url = f"https://api.telegram.org/bot{token}/sendMessage"
    info(f"Got {len(transactions)} new transactions, sending message to Telegram")
    message = "*💲 [Leggen](https://github.com/elisiariocouto/leggen)*\n"
    message += f"{len(transactions)} new transaction matches\n\n"

    for transaction in transactions:
        message += f"*Name*: {transaction['name']}\n"
        message += f"*Value*: {transaction['value']}{transaction['currency']}\n"
        message += f"*Date*: {transaction['date']}\n\n"

    res = requests.post(
        bot_url,
        json={
            "chat_id": chat_id,
            "text": escape_markdown(message),
            "parse_mode": "MarkdownV2",
        },
    )

    try:
        res.raise_for_status()
    except Exception as e:
        raise Exception(f"Telegram notification failed: {e}\n{res.text}") from e
