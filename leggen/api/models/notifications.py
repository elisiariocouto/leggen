from typing import List, Optional

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


class PushConfig(BaseModel):
    """Push notification configuration"""

    enabled: bool = True


class PushSubscription(BaseModel):
    """Push notification subscription data"""

    endpoint: str
    keys: dict  # p256dh and auth keys
    user_agent: Optional[str] = None


class NotificationFilters(BaseModel):
    """Notification filters configuration"""

    case_insensitive: List[str] = []
    case_sensitive: Optional[List[str]] = None


class NotificationSettings(BaseModel):
    """Complete notification settings"""

    discord: Optional[DiscordConfig] = None
    telegram: Optional[TelegramConfig] = None
    push: Optional[PushConfig] = None
    filters: NotificationFilters = NotificationFilters()


class NotificationTest(BaseModel):
    """Test notification request"""

    service: str  # "discord", "telegram", or "push"
    message: str = "Test notification from Leggen"


class NotificationHistory(BaseModel):
    """Notification history entry"""

    id: str
    service: str
    message: str
    status: str  # "sent", "failed"
    sent_at: str
    error: Optional[str] = None
