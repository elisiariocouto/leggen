import hmac
import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from loguru import logger

from leggen.errors import (
    AuthenticationError,
    TokenExpiredError,
    describe_exception,
)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), password_hash.encode("utf-8")
        )
    except ValueError:
        logger.warning("Malformed password hash in configuration")
        return False


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(username: str, secret: str, expires_minutes: int = 60) -> str:
    """Create a JWT access token."""
    now = datetime.now(UTC)
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_access_token(token: str, secret: str) -> str:
    """Decode a JWT access token, returning the username it identifies.

    Raises `TokenExpiredError` for a well-formed token past its expiry and
    `AuthenticationError` for anything else — a bad signature, a malformed
    token, or a payload with no `sub`. The two are kept apart so the API can
    tell a lapsed session from a credential that was never valid.
    """
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        logger.debug("Rejected an expired access token")
        raise TokenExpiredError("Session expired, please sign in again.") from exc
    except jwt.InvalidTokenError as exc:
        logger.debug(f"Rejected an invalid access token: {describe_exception(exc)}")
        raise AuthenticationError("Invalid credentials.") from exc

    username = payload.get("sub")
    if not isinstance(username, str) or not username:
        logger.debug("Rejected an access token without a subject claim")
        raise AuthenticationError("Invalid credentials.")
    return username


def verify_api_key(provided: str, configured: str) -> bool:
    """Verify an API key using constant-time comparison."""
    return hmac.compare_digest(provided, configured)


def generate_api_key() -> str:
    """Generate a random API key with lgn_ prefix."""
    return f"lgn_{secrets.token_urlsafe(32)}"


def generate_jwt_secret() -> str:
    """Generate a random JWT secret."""
    return secrets.token_urlsafe(48)
