from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from loguru import logger

from leggen.api.models.notifications import (
    DiscordConfig,
    NotificationFilters,
    NotificationSettings,
    NotificationTest,
    TelegramConfig,
)
from leggen.services.notification_service import NotificationService
from leggen.utils.config import config

router = APIRouter()
notification_service = NotificationService()


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
                webhook="***" if discord_config.get("webhook") else "",
                enabled=discord_config.get("enabled", True),
            )
            if discord_config.get("webhook")
            else None,
            telegram=TelegramConfig(
                token="***" if telegram_config.get("token") else "",
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
            status_code=500, detail=f"Failed to get notification settings: {str(e)}"
        ) from e


@router.put("/notifications/settings")
async def update_notification_settings(settings: NotificationSettings) -> dict:
    """Update notification settings"""
    try:
        # Update notifications config
        notifications_config = {}

        if settings.discord:
            notifications_config["discord"] = {
                "webhook": settings.discord.webhook,
                "enabled": settings.discord.enabled,
            }

        if settings.telegram:
            notifications_config["telegram"] = {
                "token": settings.telegram.token,
                "chat_id": settings.telegram.chat_id,
                "enabled": settings.telegram.enabled,
            }

        # Update filters config
        filters_config: Dict[str, Any] = {}
        if settings.filters.case_insensitive:
            filters_config["case_insensitive"] = settings.filters.case_insensitive
        if settings.filters.case_sensitive:
            filters_config["case_sensitive"] = settings.filters.case_sensitive

        # Save to config
        if notifications_config:
            config.update_section("notifications", notifications_config)
        if filters_config:
            config.update_section("filters", filters_config)

        return {"updated": True}

    except Exception as e:
        logger.error(f"Failed to update notification settings: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update notification settings: {str(e)}"
        ) from e


@router.post("/notifications/test")
async def test_notification(test_request: NotificationTest) -> dict:
    """Send a test notification"""
    try:
        success = await notification_service.send_test_notification(
            test_request.service, test_request.message
        )

        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to send test notification to {test_request.service}",
            )

        return {"sent": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send test notification: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to send test notification: {str(e)}"
        ) from e


@router.get("/notifications/services")
async def get_notification_services() -> dict:
    """Get available notification services and their status"""
    try:
        notifications_config = config.notifications_config

        services = {
            "discord": {
                "name": "Discord",
                "enabled": bool(notifications_config.get("discord", {}).get("webhook")),
                "configured": bool(
                    notifications_config.get("discord", {}).get("webhook")
                ),
                "active": notifications_config.get("discord", {}).get("enabled", True),
            },
            "telegram": {
                "name": "Telegram",
                "enabled": bool(
                    notifications_config.get("telegram", {}).get("token")
                    and notifications_config.get("telegram", {}).get("chat_id")
                ),
                "configured": bool(
                    notifications_config.get("telegram", {}).get("token")
                    and notifications_config.get("telegram", {}).get("chat_id")
                ),
                "active": notifications_config.get("telegram", {}).get("enabled", True),
            },
        }

        return services

    except Exception as e:
        logger.error(f"Failed to get notification services: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get notification services: {str(e)}"
        ) from e


@router.delete("/notifications/settings/{service}")
async def delete_notification_service(service: str) -> dict:
    """Delete/disable a notification service"""
    try:
        if service not in ["discord", "telegram"]:
            raise HTTPException(
                status_code=400, detail="Service must be 'discord' or 'telegram'"
            )

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
            status_code=500, detail=f"Failed to delete notification service: {str(e)}"
        ) from e
