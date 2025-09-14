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


class NotificationFilters(BaseModel):
    """Notification filters configuration"""

    case_insensitive: List[str] = []
    case_sensitive: Optional[List[str]] = None


class NotificationSettings(BaseModel):
    """Complete notification settings"""

    discord: Optional[DiscordConfig] = None
    telegram: Optional[TelegramConfig] = None
    filters: NotificationFilters = NotificationFilters()


class NotificationTest(BaseModel):
    """Test notification request"""

    service: str  # "discord" or "telegram"
    message: str = "Test notification from Leggen"


class NotificationHistory(BaseModel):
    """Notification history entry"""

    id: str
    service: str
    message: str
    status: str  # "sent", "failed"
    sent_at: str
    error: Optional[str] = None
