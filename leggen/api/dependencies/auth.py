from fastapi import Depends
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from leggen.errors import AuthenticationError
from leggen.utils.auth import decode_access_token, verify_api_key
from leggen.utils.config import config

http_bearer = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
    api_key: str | None = Depends(api_key_header),
) -> str:
    """Authenticate via JWT Bearer token or X-API-Key header."""
    auth_cfg = config.auth_config

    # Try the JWT bearer token first, remembering why it failed. A rejected
    # token must not shadow a valid X-API-Key on the same request, so the
    # failure is only raised once the key has had its turn.
    bearer_error: AuthenticationError | None = None
    if credentials:
        try:
            return decode_access_token(credentials.credentials, auth_cfg["jwt_secret"])
        except AuthenticationError as exc:
            bearer_error = exc

    # Try API key
    if api_key and verify_api_key(api_key, auth_cfg["api_key"]):
        return auth_cfg["username"]

    # An expired session and a bad credential are different problems for the
    # client, so the bearer token's own error wins when there was one.
    raise bearer_error or AuthenticationError("Invalid or missing credentials.")
