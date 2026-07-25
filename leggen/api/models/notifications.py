from typing import List, Literal, Optional

from pydantic import BaseModel


class DiscordConfig(BaseModel):
    """Discord notification configuration"""

    webhook: str
    enabled: bool = True


class TelegramConfig(BaseModel):
    """Telegram notification configuration"""

    token: str
    chat_id: int
    enabled: bool = True


class NotificationFilters(BaseModel):
    """Notification filters configuration

    Both lists are tri-state on update: omitted means "leave as stored", an
    empty list clears that list, and a populated list replaces it.
    """

    case_insensitive: Optional[List[str]] = None
    case_sensitive: Optional[List[str]] = None


class NotificationSettings(BaseModel):
    """Complete notification settings

    Every field is optional so that an update can address one part of the
    settings without disturbing the rest; see the PUT handler in
    `api/routes/notifications.py` for the merge semantics.
    """

    discord: Optional[DiscordConfig] = None
    telegram: Optional[TelegramConfig] = None
    filters: Optional[NotificationFilters] = None


class NotificationTest(BaseModel):
    """Test notification request"""

    service: Literal["discord", "telegram"]
