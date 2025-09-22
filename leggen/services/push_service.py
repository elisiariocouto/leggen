import json
from typing import Any, Dict, List, Optional

from loguru import logger
from pywebpush import WebPushException, webpush

from leggen.utils.config import config
from leggen.utils.paths import path_manager


class PushService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self.subscriptions: List[Dict[str, Any]] = config.notifications_config.get(
                "push_subscriptions", []
            )
            self.vapid_keys: Optional[Dict[str, str]] = None
            self._load_or_generate_vapid_keys()
            self._initialized = True

    def _get_vapid_keys_path(self) -> str:
        """Get the path to the VAPID keys file"""
        return str(path_manager.get_database_path().parent / "vapid_keys.json")

    def _load_or_generate_vapid_keys(self) -> None:
        """Load VAPID keys from file or generate new ones"""
        keys_path = self._get_vapid_keys_path()

        try:
            with open(keys_path, "r") as f:
                loaded_keys = json.load(f)
                # Validate that we have the expected keys and they are strings (PEM format)
                if (
                    isinstance(loaded_keys, dict)
                    and "public_key" in loaded_keys
                    and "private_key" in loaded_keys
                    and isinstance(loaded_keys["public_key"], str)
                    and isinstance(loaded_keys["private_key"], str)
                    and loaded_keys["public_key"].startswith(
                        "-----BEGIN PUBLIC KEY-----"
                    )
                    and loaded_keys["private_key"].startswith(
                        "-----BEGIN PRIVATE KEY-----"
                    )
                ):
                    self.vapid_keys = loaded_keys
                    logger.info("VAPID keys loaded from file")
                else:
                    raise ValueError("Invalid VAPID keys format")
        except (FileNotFoundError, json.JSONDecodeError, ValueError, KeyError):
            logger.info("VAPID keys not found or invalid, generating new ones")
            self.vapid_keys = self.generate_vapid_keys()
            self._save_vapid_keys()

    def _save_vapid_keys(self) -> None:
        """Save VAPID keys to file"""
        if self.vapid_keys is None:
            return

        keys_path = self._get_vapid_keys_path()
        try:
            with open(keys_path, "w") as f:
                json.dump(self.vapid_keys, f, indent=2)
            logger.info("VAPID keys saved to file")
        except Exception as e:
            logger.error(f"Failed to save VAPID keys: {e}")

    def generate_vapid_keys(self) -> Dict[str, str]:
        """Generate VAPID key pair for push notifications"""
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.asymmetric import ec
        from pywebpush import Vapid

        # Generate ECDSA private key
        private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())

        # Create Vapid object with the private key
        vapid = Vapid(private_key=private_key)

        return {
            "public_key": vapid.public_pem().decode("utf-8"),
            "private_key": vapid.private_pem().decode("utf-8"),
        }

    def get_vapid_public_key(self) -> Optional[str]:
        """Get the VAPID public key for client-side subscription"""
        return self.vapid_keys.get("public_key") if self.vapid_keys else None

    def is_push_enabled(self) -> bool:
        """Check if push notifications are enabled"""
        return bool(self.vapid_keys and self.vapid_keys.get("private_key"))

    def add_subscription(self, subscription: Dict[str, Any]) -> None:
        """Add a push subscription"""
        # Check if subscription already exists
        existing = next(
            (
                s
                for s in self.subscriptions
                if s.get("endpoint") == subscription.get("endpoint")
            ),
            None,
        )

        if existing:
            # Update existing subscription
            existing.update(subscription)
        else:
            # Add new subscription
            self.subscriptions.append(subscription)

        # Save to config
        notifications_config = config.notifications_config.copy()
        notifications_config["push_subscriptions"] = self.subscriptions
        config.update_section("notifications", notifications_config)

        logger.info(
            f"Added push subscription for endpoint: {subscription.get('endpoint')}"
        )

    def remove_subscription(self, endpoint: str) -> None:
        """Remove a push subscription"""
        self.subscriptions = [
            s for s in self.subscriptions if s.get("endpoint") != endpoint
        ]

        # Save to config
        notifications_config = config.notifications_config.copy()
        notifications_config["push_subscriptions"] = self.subscriptions
        config.update_section("notifications", notifications_config)

        logger.info(f"Removed push subscription for endpoint: {endpoint}")

    def send_push_notification(
        self, title: str, body: str, url: str = "/", icon: str = "/pwa-192x192.png"
    ) -> bool:
        """Send push notification to all subscribed clients"""
        if not self.is_push_enabled():
            logger.info("Push notifications not enabled")
            return False

        if not self.subscriptions:
            logger.info("No push subscriptions found")
            return False

        vapid_private_key = (
            self.vapid_keys.get("private_key") if self.vapid_keys else None
        )
        vapid_claims = {"sub": "mailto:admin@leggen.app"}

        message = {
            "title": title,
            "body": body,
            "icon": icon,
            "badge": "/pwa-64x64.png",
            "data": {"url": url},
        }

        success_count = 0
        for subscription in self.subscriptions:
            try:
                webpush(
                    subscription_info=subscription,
                    data=json.dumps(message),
                    vapid_private_key=vapid_private_key,
                    vapid_claims=vapid_claims,
                )
                success_count += 1
            except WebPushException as e:
                logger.error(
                    f"Failed to send push notification to {subscription.get('endpoint')}: {e}"
                )
                # Remove invalid subscriptions
                if "410" in str(e) or "400" in str(e):  # Gone or Bad Request
                    self.remove_subscription(subscription.get("endpoint", ""))

        logger.info(
            f"Sent push notification to {success_count}/{len(self.subscriptions)} subscribers"
        )
        return success_count > 0

    def send_test_notification(self, message: str) -> bool:
        """Send test push notification"""
        return self.send_push_notification(
            title="Test Notification",
            body=message,
            url="/notifications",
            icon="/pwa-192x192.png",
        )

    def send_transaction_notification(
        self, transaction_count: int, total_value: float, currency: str
    ) -> bool:
        """Send transaction notification"""
        return self.send_push_notification(
            title=f"New Transactions ({transaction_count})",
            body=f"Total: {total_value:.2f} {currency}",
            url="/transactions",
            icon="/pwa-192x192.png",
        )

    def send_expiry_notification(
        self, bank: str, requisition_id: str, status: str, days_left: int
    ) -> bool:
        """Send account expiry notification"""
        return self.send_push_notification(
            title="Account Expiration Notice",
            body=f"Your account {bank} ({requisition_id}) is in {status} status. Days left: {days_left}",
            url="/settings",
            icon="/pwa-192x192.png",
        )
