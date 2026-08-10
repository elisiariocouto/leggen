import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
import jwt
from loguru import logger

from leggen.utils.config import config

# States issued by start_auth, awaiting the bank redirect. Module-level so
# they are shared across all service instances (routes and sync service).
_pending_auth_states: Dict[str, float] = {}


class EnableBankingService:
    JWT_TTL_SECONDS = 3600
    ASPSPS_CACHE_TTL_SECONDS = 3600
    AUTH_STATE_TTL_SECONDS = 3600

    def __init__(self):
        self._private_key: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None
        self._client_timeout: Optional[httpx.Timeout] = None
        self._jwt_token: Optional[str] = None
        self._jwt_expires_at: float = 0.0
        self._aspsps_cache: Dict[str, tuple[float, list[Dict[str, Any]]]] = {}

    # Config is read live via properties (not cached at construction) so
    # settings changes apply without a server restart.
    @property
    def config(self) -> Dict[str, Any]:
        return config.enablebanking_config

    @property
    def base_url(self) -> str:
        return self.config.get("url", "https://api.enablebanking.com")

    @property
    def timeout(self) -> httpx.Timeout:
        """Per-request timeouts for EnableBanking calls.

        Read is granted a longer budget than connect because the upstream API
        is slow to produce large transaction pages; a single stalled page would
        otherwise abort the whole account sync.
        """
        return httpx.Timeout(
            connect=float(self.config.get("connect_timeout") or 10.0),
            read=float(self.config.get("read_timeout") or 60.0),
            write=10.0,
            pool=10.0,
        )

    def _get_client(self) -> httpx.AsyncClient:
        """Return the shared HTTP client, creating it on first use.

        Recreated when the configured timeout changes so settings edits apply
        without a server restart, matching the live-config properties above.
        """
        timeout = self.timeout
        if (
            self._client is None
            or self._client.is_closed
            or self._client_timeout != timeout
        ):
            self._client = httpx.AsyncClient(timeout=timeout)
            self._client_timeout = timeout
        return self._client

    def _load_private_key(self) -> str:
        """Load RSA private key from the configured file path."""
        if self._private_key is None:
            key_path = Path(self.config["key_path"])
            self._private_key = key_path.read_text()
        return self._private_key

    def _generate_jwt(self) -> str:
        """Return a JWT for EnableBanking API auth, cached until near expiry."""
        now = time.time()
        if self._jwt_token is not None and now < self._jwt_expires_at - 60:
            return self._jwt_token

        application_id = self.config["application_id"]
        private_key = self._load_private_key()
        iat = int(now)

        payload = {
            "iss": "enablebanking.com",
            "aud": "api.enablebanking.com",
            "iat": iat,
            "exp": iat + self.JWT_TTL_SECONDS,
        }

        headers = {
            "kid": application_id,
        }

        self._jwt_token = jwt.encode(
            payload, private_key, algorithm="RS256", headers=headers
        )
        self._jwt_expires_at = iat + self.JWT_TTL_SECONDS
        return self._jwt_token

    async def _make_request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Make an authenticated request to the EnableBanking API."""
        token = self._generate_jwt()
        url = f"{self.base_url}{path}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        response = await self._get_client().request(
            method, url, headers=headers, **kwargs
        )
        logger.debug(f"{method} {url} -> {response.status_code}")
        if response.status_code >= 400:
            logger.error(f"{method} {url} error response body: {response.text}")
        response.raise_for_status()
        result = response.json()
        logger.debug(f"{method} {url} response: {result}")
        return result

    async def get_aspsps(self, country: str) -> list[Dict[str, Any]]:
        """Get available ASPSPs (banks) for a country, cached per country."""
        cached = self._aspsps_cache.get(country)
        if cached and time.time() - cached[0] < self.ASPSPS_CACHE_TTL_SECONDS:
            return cached[1]

        result = await self._make_request("GET", "/aspsps", params={"country": country})
        aspsps = result.get("aspsps", [])
        self._aspsps_cache[country] = (time.time(), aspsps)
        return aspsps

    async def start_auth(
        self,
        aspsp_name: str,
        aspsp_country: str,
        redirect_url: str,
        psu_type: str = "personal",
        valid_until: Optional[str] = None,
        maximum_consent_validity: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Start user authorization flow. Returns a dict with 'url' for redirect."""
        if not valid_until:
            if maximum_consent_validity:
                dt = datetime.now(timezone.utc) + timedelta(
                    seconds=maximum_consent_validity
                )
            else:
                dt = datetime.now(timezone.utc) + timedelta(days=90)
            valid_until = dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        state = str(uuid.uuid4())
        self._register_auth_state(state)
        body: Dict[str, Any] = {
            "aspsp": {"name": aspsp_name, "country": aspsp_country},
            "state": state,
            "redirect_url": redirect_url,
            "psu_type": psu_type,
            "access": {
                "valid_until": valid_until,
                "balances": True,
                "transactions": True,
            },
        }

        return await self._make_request("POST", "/auth", json=body)

    def _register_auth_state(self, state: str) -> None:
        """Track a state issued to the bank so the callback can verify it."""
        now = time.time()
        # Drop states that were never redeemed
        for pending, issued_at in list(_pending_auth_states.items()):
            if now - issued_at > self.AUTH_STATE_TTL_SECONDS:
                del _pending_auth_states[pending]
        _pending_auth_states[state] = now

    def consume_auth_state(self, state: str) -> bool:
        """Redeem a state from a bank redirect. Each state is single-use."""
        issued_at = _pending_auth_states.pop(state, None)
        return (
            issued_at is not None
            and time.time() - issued_at <= self.AUTH_STATE_TTL_SECONDS
        )

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()

    async def create_session(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for a session."""
        return await self._make_request("POST", "/sessions", json={"code": code})

    async def get_account_details(self, account_id: str) -> Dict[str, Any]:
        """Get account details."""
        return await self._make_request("GET", f"/accounts/{account_id}/details")

    async def get_account_balances(self, account_id: str) -> Dict[str, Any]:
        """Get account balances."""
        return await self._make_request("GET", f"/accounts/{account_id}/balances")

    async def get_account_transactions(
        self, account_id: str, date_from: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get account transactions with automatic pagination."""
        params: Dict[str, str] = {}
        if date_from:
            params["date_from"] = date_from

        all_transactions: list[Dict[str, Any]] = []

        while True:
            result = await self._make_request(
                "GET", f"/accounts/{account_id}/transactions", params=params
            )
            all_transactions.extend(result.get("transactions", []))

            continuation_key = result.get("continuation_key")
            if not continuation_key:
                break

            params["continuation_key"] = continuation_key

        return {"transactions": all_transactions}


# Application-scoped instance for FastAPI routes. A per-request instance
# (bare Depends()) would leak an unclosed httpx.AsyncClient per request and
# defeat the JWT and ASPSP caches.
_service: Optional[EnableBankingService] = None
# Sync dependencies run in FastAPI's threadpool, so creation must be locked.
_service_lock = threading.Lock()


def get_enablebanking_service() -> EnableBankingService:
    """FastAPI dependency returning the app-scoped service instance."""
    global _service
    if _service is None:
        with _service_lock:
            if _service is None:
                _service = EnableBankingService()
    return _service


async def close_enablebanking_service() -> None:
    """Close the app-scoped service's HTTP client (lifespan shutdown)."""
    global _service
    if _service is not None:
        await _service.aclose()
        _service = None
