from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from leggen.utils.auth import create_access_token, verify_password
from leggen.utils.config import config

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthStatusResponse(BaseModel):
    auth_enabled: bool


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    """Authenticate with username and password, returns JWT token."""
    auth_cfg = config.auth_config

    if request.username != auth_cfg["username"] or not verify_password(
        request.password, auth_cfg["password_hash"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token(
        username=request.username,
        secret=auth_cfg["jwt_secret"],
        expires_minutes=auth_cfg.get("jwt_expiry_minutes", 60),
    )

    return LoginResponse(access_token=token)


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status() -> AuthStatusResponse:
    """Check if authentication is enabled (always true)."""
    return AuthStatusResponse(auth_enabled=True)
