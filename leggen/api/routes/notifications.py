from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from loguru import logger

from leggen.api.models.common import APIResponse
from leggen.api.models.notifications import (
    DiscordConfig,
    NotificationFilters,
    NotificationSettings,
    NotificationTest,
    PushConfig,
    PushSubscription,
    TelegramConfig,
)
from leggen.services.notification_service import NotificationService
from leggen.services.push_service import PushService
from leggen.utils.config import config

router = APIRouter()
notification_service = NotificationService()
push_service = PushService()


@router.get("/notifications/settings", response_model=APIResponse)
async def get_notification_settings() -> APIResponse:
    """Get current notification settings"""
    try:
        notifications_config = config.notifications_config
        filters_config = config.filters_config

        # Build response safely without exposing secrets
        discord_config = notifications_config.get("discord", {})
        telegram_config = notifications_config.get("telegram", {})
        push_config = notifications_config.get("push", {})

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
            push=PushConfig(
                enabled=push_config.get("enabled", True),
            )
            if push_config
            else None,
            filters=NotificationFilters(
                case_insensitive=filters_config.get("case_insensitive", []),
                case_sensitive=filters_config.get("case_sensitive"),
            ),
        )

        return APIResponse(
            success=True,
            data=settings,
            message="Notification settings retrieved successfully",
        )

    except Exception as e:
        logger.error(f"Failed to get notification settings: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get notification settings: {str(e)}"
        ) from e


@router.put("/notifications/settings", response_model=APIResponse)
async def update_notification_settings(settings: NotificationSettings) -> APIResponse:
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

        if settings.push:
            notifications_config["push"] = {
                "enabled": settings.push.enabled,
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

        return APIResponse(
            success=True,
            data={"updated": True},
            message="Notification settings updated successfully",
        )

    except Exception as e:
        logger.error(f"Failed to update notification settings: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update notification settings: {str(e)}"
        ) from e


@router.post("/notifications/test", response_model=APIResponse)
async def test_notification(test_request: NotificationTest) -> APIResponse:
    """Send a test notification"""
    try:
        success = await notification_service.send_test_notification(
            test_request.service, test_request.message
        )

        if success:
            return APIResponse(
                success=True,
                data={"sent": True},
                message=f"Test notification sent to {test_request.service} successfully",
            )
        else:
            return APIResponse(
                success=False,
                message=f"Failed to send test notification to {test_request.service}",
            )

    except Exception as e:
        logger.error(f"Failed to send test notification: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to send test notification: {str(e)}"
        ) from e


@router.get("/notifications/services", response_model=APIResponse)
async def get_notification_services() -> APIResponse:
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
            "push": {
                "name": "Push Notifications",
                "enabled": bool(
                    push_service.is_push_enabled()
                    and len(push_service.subscriptions) > 0
                ),
                "configured": push_service.is_push_enabled(),
                "active": notifications_config.get("push", {}).get("enabled", True),
            },
        }

        return APIResponse(
            success=True,
            data=services,
            message="Notification services status retrieved successfully",
        )

    except Exception as e:
        logger.error(f"Failed to get notification services: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get notification services: {str(e)}"
        ) from e


@router.delete("/notifications/settings/{service}", response_model=APIResponse)
async def delete_notification_service(service: str) -> APIResponse:
    """Delete/disable a notification service"""
    try:
        if service not in ["discord", "telegram", "push"]:
            raise HTTPException(
                status_code=400,
                detail="Service must be 'discord', 'telegram', or 'push'",
            )

        notifications_config = config.notifications_config.copy()
        if service in notifications_config:
            del notifications_config[service]
            config.update_section("notifications", notifications_config)

        return APIResponse(
            success=True,
            data={"deleted": service},
            message=f"{service.capitalize()} notification service deleted successfully",
        )

    except Exception as e:
        logger.error(f"Failed to delete notification service {service}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete notification service: {str(e)}"
        ) from e


@router.post("/notifications/push/subscribe", response_model=APIResponse)
async def subscribe_push_notifications(subscription: PushSubscription) -> APIResponse:
    """Subscribe to push notifications"""
    try:
        push_service.add_subscription(subscription.dict())

        return APIResponse(
            success=True,
            data={"subscribed": True},
            message="Successfully subscribed to push notifications",
        )

    except Exception as e:
        logger.error(f"Failed to subscribe to push notifications: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to subscribe to push notifications: {str(e)}",
        ) from e


@router.post("/notifications/push/unsubscribe", response_model=APIResponse)
async def unsubscribe_push_notifications(subscription: PushSubscription) -> APIResponse:
    """Unsubscribe from push notifications"""
    try:
        push_service.remove_subscription(subscription.endpoint)

        return APIResponse(
            success=True,
            data={"unsubscribed": True},
            message="Successfully unsubscribed from push notifications",
        )

    except Exception as e:
        logger.error(f"Failed to unsubscribe from push notifications: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to unsubscribe from push notifications: {str(e)}",
        ) from e


@router.get("/notifications/push/public-key", response_model=APIResponse)
async def get_push_public_key() -> APIResponse:
    """Get VAPID public key for push notification subscription"""
    try:
        public_key = push_service.get_vapid_public_key()

        if not public_key:
            return APIResponse(
                success=False,
                message="Push notifications not configured",
            )

        return APIResponse(
            success=True,
            data={"public_key": public_key},
            message="VAPID public key retrieved successfully",
        )

    except Exception as e:
        logger.error(f"Failed to get VAPID public key: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get VAPID public key: {str(e)}"
        ) from e
