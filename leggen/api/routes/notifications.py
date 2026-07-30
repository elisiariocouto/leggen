from typing import Any, Dict, Literal

from fastapi import APIRouter, HTTPException
from loguru import logger

from leggen.api.models.notifications import (
    DiscordConfig,
    NotificationFilters,
    NotificationSettings,
    NotificationTest,
    TelegramConfig,
)
from leggen.errors import LeggenError
from leggen.services.notification_service import NotificationService
from leggen.utils.config import config
from leggen.utils.masking import MaskedSecretError, mask_secret, resolve_secret

router = APIRouter()


@router.get("/notifications/settings")
async def get_notification_settings() -> NotificationSettings:
    """Get current notification settings"""
    try:
        notifications_config = config.notifications_config
        filters_config = config.filters_config

        # Build response safely without exposing secrets
        discord_config = notifications_config.get("discord", {})
        telegram_config = notifications_config.get("telegram", {})

        settings = NotificationSettings(
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

        return settings

    except Exception as e:
        logger.error(f"Failed to get notification settings: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get notification settings."
        ) from e


@router.put("/notifications/settings")
async def update_notification_settings(settings: NotificationSettings) -> dict:
    """Update notification settings

    Fields absent from the request body are left as stored; `update_section`
    replaces a section wholesale, so merging here is what keeps a partial body
    from wiping the settings it does not mention. An explicit `null` service
    removes it, and an explicit empty filter list clears it.
    """
    try:
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
            filters_config: Dict[str, Any] = dict(config.filters_config)
            for field in ("case_insensitive", "case_sensitive"):
                if field in settings.filters.model_fields_set:
                    filters_config[field] = getattr(settings.filters, field) or []
            config.update_section("filters", filters_config)

        return {"updated": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update notification settings: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to update notification settings."
        ) from e


@router.post("/notifications/test")
async def test_notification(test_request: NotificationTest) -> dict:
    """Send a test notification.

    Distinguishes a misconfiguration (``NOTIFICATION_NOT_ENABLED``, 400) from
    an upstream provider failure (``NOTIFICATION_SEND_FAILED``, 502) — both are
    raised as domain errors by the service and rendered by the global handler.
    """
    try:
        await NotificationService().send_test_notification(test_request.service)
        return {"sent": True}

    except (HTTPException, LeggenError):
        raise
    except Exception as e:
        logger.error(f"Failed to send test notification: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to send test notification."
        ) from e


@router.get("/notifications/services")
async def get_notification_services() -> dict:
    """Get available notification services and their status"""
    try:
        notifications_config = config.notifications_config

        discord = notifications_config.get("discord", {})
        telegram = notifications_config.get("telegram", {})

        # `configured` = has credentials; `enabled` = the on/off toggle
        # (default on); `active` = both, i.e. actually operational. Keeping the
        # three distinct is what makes the frontend's "Needs Configuration"
        # (enabled but not configured) and "Disabled" (toggled off) states
        # reachable.
        discord_configured = bool(discord.get("webhook"))
        discord_enabled = bool(discord.get("enabled", True))
        telegram_configured = bool(telegram.get("token") and telegram.get("chat_id"))
        telegram_enabled = bool(telegram.get("enabled", True))

        services = {
            "discord": {
                "name": "Discord",
                "enabled": discord_enabled,
                "configured": discord_configured,
                "active": discord_enabled and discord_configured,
            },
            "telegram": {
                "name": "Telegram",
                "enabled": telegram_enabled,
                "configured": telegram_configured,
                "active": telegram_enabled and telegram_configured,
            },
        }

        return services

    except Exception as e:
        logger.error(f"Failed to get notification services: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get notification services."
        ) from e


# Declared before the /{service} route below, which would otherwise match
# "filters" and reject it as an unknown service.
@router.delete("/notifications/settings/filters")
async def delete_notification_filters() -> dict:
    """Remove all notification filters"""
    try:
        config.update_section("filters", {})

        return {"deleted": "filters"}

    except Exception as e:
        logger.error(f"Failed to delete notification filters: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to delete notification filters."
        ) from e


@router.delete("/notifications/settings/{service}")
async def delete_notification_service(
    service: Literal["discord", "telegram"],
) -> dict:
    """Delete/disable a notification service

    The ``Literal`` path type validates the service name for us, yielding a 422
    for anything else — consistent with the test endpoint rather than the old
    hand-rolled 400.
    """
    try:
        notifications_config = config.notifications_config.copy()
        if service in notifications_config:
            del notifications_config[service]
            config.update_section("notifications", notifications_config)

        return {"deleted": service}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete notification service {service}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to delete notification service."
        ) from e
