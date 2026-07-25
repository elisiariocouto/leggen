import httpx

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


async def _send_message(token: str, chat_id: str, message: str) -> None:
    bot_url = f"https://api.telegram.org/bot{token}/sendMessage"
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            bot_url,
            json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "MarkdownV2",
            },
        )
        if response.status_code >= 400:
            raise Exception(
                f"Telegram notification failed: {response.status_code}\n{response.text}"
            )


async def send_expire_notification(token: str, chat_id: str, notification: dict):
    info("Sending expiration notification to Telegram")
    message = "*💲 [Leggen](https://github.com/elisiariocouto/leggen)*\n"
    message += escape_markdown(
        f"Your account {notification['bank']} ({notification['session_id']}) is in {notification['status']} status. Days left: {notification['days_left']}\n"
    )
    await _send_message(token, chat_id, message)


async def send_test_notification(token: str, chat_id: str):
    info("Sending test notification to Telegram")
    message = "*🔔 [Leggen](https://github.com/elisiariocouto/leggen)*\n"
    message += escape_markdown("Leggen notifications are configured correctly.")
    await _send_message(token, chat_id, message)


async def send_transaction_message(token: str, chat_id: str, transactions: list):
    info(f"Got {len(transactions)} new transactions, sending message to Telegram")
    message = "*💲 [Leggen](https://github.com/elisiariocouto/leggen)*\n"
    message += f"{len(transactions)} new transaction matches\n\n"

    for transaction in transactions:
        message += f"*Name*: {escape_markdown(transaction['name'])}\n"
        message += f"*Value*: {escape_markdown(transaction['value'])}{escape_markdown(transaction['currency'])}\n"
        message += f"*Date*: {escape_markdown(transaction['date'])}\n\n"

    await _send_message(token, chat_id, message)


async def send_sync_failure_notification(token: str, chat_id: str, notification: dict):
    info("Sending sync failure notification to Telegram")

    message = "*⚠️ [Leggen](https://github.com/elisiariocouto/leggen)*\n"
    message += "*Sync Failed*\n\n"

    if notification.get("account_id"):
        message += escape_markdown(f"Account: {notification['account_id']}\n")

    message += escape_markdown(f"Error: {notification['error']}\n")

    await _send_message(token, chat_id, message)
