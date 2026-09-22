from typing import Any, Literal

from fastapi import APIRouter

from leggen.api.models.notifications import (
    DiscordConfig,
    NotificationFilters,
    NotificationServiceStatus,
    NotificationSettings,
    NotificationTest,
    TelegramConfig,
)
from leggen.services.notification_service import NotificationService
from leggen.utils.config import config
from leggen.utils.masking import mask_secret, resolve_secret

router = APIRouter()

# Each service's secret field, and how errors name it.
_SECRETS = {
    "discord": ("webhook", "Discord webhook"),
    "telegram": ("token", "Telegram token"),
}


def _with_stored_secret(
    service: str, section: DiscordConfig | TelegramConfig
) -> dict[str, Any]:
    """The section as a dict, its secret resolved against the stored one.

    Clients echo back the masked secret from GET to mean "keep the current
    value"; a mask with nothing stored raises MaskedSecretError, a 400.
    """
    field, label = _SECRETS[service]
    stored = config.notifications_config.get(service, {}).get(field)
    secret = resolve_secret(getattr(section, field), stored, label)
    return section.model_copy(update={field: secret}).model_dump()


@router.get("/notifications/settings")
async def get_notification_settings() -> NotificationSettings:
    """Get current notification settings"""
    notifications_config = config.notifications_config
    filters_config = config.filters_config

    # Build response safely without exposing secrets
    discord_config = notifications_config.get("discord", {})
    telegram_config = notifications_config.get("telegram", {})

    return NotificationSettings(
        discord=DiscordConfig(
            webhook=mask_secret(discord_config.get("webhook")),
            enabled=discord_config.get("enabled", True),
        )
        if discord_config.get("webhook")
        else None,
        telegram=TelegramConfig(
            token=mask_secret(telegram_config.get("token")),
            chat_id=telegram_config.get("chat_id", 0),
            enabled=telegram_config.get("enabled", True),
        )
        if telegram_config.get("token")
        else None,
        filters=NotificationFilters(
            case_insensitive=filters_config.get("case_insensitive", []),
            case_sensitive=filters_config.get("case_sensitive"),
        ),
    )


@router.put("/notifications/settings")
async def update_notification_settings(settings: NotificationSettings) -> dict:
    """Update notification settings

    Fields absent from the request body are left as stored; `update_section`
    replaces a section wholesale, so merging here is what keeps a partial body
    from wiping the settings it does not mention. An explicit `null` service
    removes it, and an explicit empty filter list clears it.
    """
    stored_config = config.notifications_config
    notifications_config = dict(stored_config)

    for service in ("discord", "telegram"):
        if service not in settings.model_fields_set:
            continue
        section = getattr(settings, service)
        if section is None:
            notifications_config.pop(service, None)
        else:
            notifications_config[service] = _with_stored_secret(service, section)

    if notifications_config != stored_config:
        config.update_section("notifications", notifications_config)

    # `exclude_none` on save would drop a null list, so cleared filters are
    # written as empty lists rather than None.
    if settings.filters is not None:
        filters_config: dict[str, Any] = dict(config.filters_config)
        for field in ("case_insensitive", "case_sensitive"):
            if field in settings.filters.model_fields_set:
                filters_config[field] = getattr(settings.filters, field) or []
        config.update_section("filters", filters_config)

    return {"updated": True}


@router.post("/notifications/test")
async def test_notification(test_request: NotificationTest) -> dict:
    """Send a test notification

    The service raises `NotificationNotEnabledError` (400) when the service is
    unconfigured or switched off, and `UpstreamServiceError` (502) when the
    provider itself refuses the message, so clients can tell a settings problem
    apart from a transient delivery failure.
    """
    section = (
        _with_stored_secret(test_request.service, test_request.config)
        if test_request.config is not None
        else None
    )
    await NotificationService().send_test_notification(test_request.service, section)

    return {"sent": True}


@router.get("/notifications/services")
async def get_notification_services() -> dict[str, NotificationServiceStatus]:
    """Get available notification services and their status"""
    notifications_config = config.notifications_config
    discord = notifications_config.get("discord", {})
    telegram = notifications_config.get("telegram", {})
    discord_configured = bool(discord.get("webhook"))
    telegram_configured = bool(telegram.get("token") and telegram.get("chat_id"))
    discord_enabled = bool(discord.get("enabled", True))
    telegram_enabled = bool(telegram.get("enabled", True))

    # `enabled` is the user's on/off switch and `configured` says whether the
    # credentials are present; `active` is the conjunction, and matches what
    # NotificationService actually requires before sending.
    return {
        "discord": NotificationServiceStatus(
            name="Discord",
            enabled=discord_enabled,
            configured=discord_configured,
            active=discord_enabled and discord_configured,
        ),
        "telegram": NotificationServiceStatus(
            name="Telegram",
            enabled=telegram_enabled,
            configured=telegram_configured,
            active=telegram_enabled and telegram_configured,
        ),
    }


@router.delete("/notifications/settings/{service}")
async def delete_notification_service(
    service: Literal["discord", "telegram"],
) -> dict:
    """Delete/disable a notification service

    The service name is validated by FastAPI against the Literal, so an unknown
    one is a 422 in the same envelope as the test endpoint's.
    """
    notifications_config = config.notifications_config.copy()
    if service in notifications_config:
        del notifications_config[service]
        config.update_section("notifications", notifications_config)

    return {"deleted": service}
