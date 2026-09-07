from typing import Any, Literal

from fastapi import APIRouter, HTTPException

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
from leggen.utils.masking import MaskedSecretError, mask_secret, resolve_secret

router = APIRouter()


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
    # Clients echo back masked secrets from GET to mean "keep current value"
    stored_config = config.notifications_config
    notifications_config = dict(stored_config)

    if "discord" in settings.model_fields_set:
        if settings.discord is None:
            notifications_config.pop("discord", None)
        else:
            try:
                webhook = resolve_secret(
                    settings.discord.webhook,
                    stored_config.get("discord", {}).get("webhook"),
                    "Discord webhook",
                )
            except MaskedSecretError as e:
                raise HTTPException(status_code=400, detail=str(e)) from e
            notifications_config["discord"] = {
                "webhook": webhook,
                "enabled": settings.discord.enabled,
            }

    if "telegram" in settings.model_fields_set:
        if settings.telegram is None:
            notifications_config.pop("telegram", None)
        else:
            try:
                token = resolve_secret(
                    settings.telegram.token,
                    stored_config.get("telegram", {}).get("token"),
                    "Telegram token",
                )
            except MaskedSecretError as e:
                raise HTTPException(status_code=400, detail=str(e)) from e
            notifications_config["telegram"] = {
                "token": token,
                "chat_id": settings.telegram.chat_id,
                "enabled": settings.telegram.enabled,
            }

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
    await NotificationService().send_test_notification(test_request.service)

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


# Declared before the /{service} route below, which would otherwise match
# "filters" and reject it as an unknown service.
@router.delete("/notifications/settings/filters")
async def delete_notification_filters() -> dict:
    """Remove all notification filters"""
    config.update_section("filters", {})

    return {"deleted": "filters"}


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
