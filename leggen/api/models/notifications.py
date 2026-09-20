from typing import Literal

from pydantic import BaseModel

from leggen.models.config import DiscordNotificationConfig, TelegramNotificationConfig


class DiscordConfig(DiscordNotificationConfig):
    """The Discord section as the API exchanges it: the webhook is masked on
    reads, and a masked value on writes keeps the stored one."""


class TelegramConfig(TelegramNotificationConfig):
    """The Telegram section as the API exchanges it: the token is masked on
    reads, and a masked value on writes keeps the stored one."""


class NotificationFilters(BaseModel):
    """Notification filters configuration

    Both lists are tri-state on update: omitted means "leave as stored", an
    empty list clears that list, and a populated list replaces it.
    """

    case_insensitive: list[str] | None = None
    case_sensitive: list[str] | None = None


class NotificationServiceStatus(BaseModel):
    """Availability and configuration state of one notification service"""

    name: str
    enabled: bool
    configured: bool
    active: bool


class NotificationSettings(BaseModel):
    """Complete notification settings

    Every field is optional so that an update can address one part of the
    settings without disturbing the rest; see the PUT handler in
    `api/routes/notifications.py` for the merge semantics.
    """

    discord: DiscordConfig | None = None
    telegram: TelegramConfig | None = None
    filters: NotificationFilters | None = None


class NotificationTest(BaseModel):
    """Test notification request"""

    service: Literal["discord", "telegram"]
