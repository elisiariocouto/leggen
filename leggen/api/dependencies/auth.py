from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from leggen.utils.auth import decode_access_token, verify_api_key
from leggen.utils.config import config

http_bearer = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    api_key: Optional[str] = Depends(api_key_header),
) -> str:
    """Authenticate via JWT Bearer token or X-API-Key header."""
    auth_cfg = config.auth_config

    # Try JWT Bearer token first
    if credentials:
        username = decode_access_token(credentials.credentials, auth_cfg["jwt_secret"])
        if username:
            return username

    # Try API key
    if api_key and verify_api_key(api_key, auth_cfg["api_key"]):
        return auth_cfg["username"]

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
