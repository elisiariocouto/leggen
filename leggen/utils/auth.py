import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(username: str, secret: str, expires_minutes: int = 60) -> str:
    """Create a JWT access token."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_access_token(token: str, secret: str) -> Optional[str]:
    """Decode a JWT access token. Returns username or None if invalid."""
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload.get("sub")
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def verify_api_key(provided: str, configured: str) -> bool:
    """Verify an API key using constant-time comparison."""
    return hmac.compare_digest(provided, configured)


def generate_api_key() -> str:
    """Generate a random API key with lgn_ prefix."""
    return f"lgn_{secrets.token_urlsafe(32)}"


def generate_jwt_secret() -> str:
    """Generate a random JWT secret."""
    return secrets.token_urlsafe(48)
