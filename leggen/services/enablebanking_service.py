import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
import jwt
from loguru import logger

from leggen.utils.config import config


class EnableBankingService:
    def __init__(self):
        self.config = config.enablebanking_config
        self.base_url = self.config.get("url", "https://api.enablebanking.com")
        self._private_key: Optional[str] = None

    def _load_private_key(self) -> str:
        """Load RSA private key from the configured file path."""
        if self._private_key is None:
            key_path = Path(self.config["key_path"])
            self._private_key = key_path.read_text()
        return self._private_key

    def _generate_jwt(self) -> str:
        """Generate a JWT token for EnableBanking API authentication."""
        application_id = self.config["application_id"]
        private_key = self._load_private_key()
        now = int(time.time())

        payload = {
            "iss": "enablebanking.com",
            "aud": "api.enablebanking.com",
            "iat": now,
            "exp": now + 3600,
        }

        headers = {
            "kid": application_id,
        }

        return jwt.encode(payload, private_key, algorithm="RS256", headers=headers)

    async def _make_request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Make an authenticated request to the EnableBanking API."""
        token = self._generate_jwt()
        url = f"{self.base_url}{path}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method, url, headers=headers, timeout=30, **kwargs
            )
            logger.debug(f"{method} {url} -> {response.status_code}")
            if response.status_code >= 400:
                logger.error(f"{method} {url} error response body: {response.text}")
            response.raise_for_status()
            result = response.json()
            logger.debug(f"{method} {url} response: {result}")
            return result

    async def get_aspsps(self, country: str) -> list[Dict[str, Any]]:
        """Get available ASPSPs (banks) for a country."""
        result = await self._make_request("GET", "/aspsps", params={"country": country})
        return result.get("aspsps", [])

    async def start_auth(
        self,
        aspsp_name: str,
        aspsp_country: str,
        redirect_url: str,
        valid_until: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Start user authorization flow. Returns a dict with 'url' for redirect."""
        state = str(uuid.uuid4())
        body: Dict[str, Any] = {
            "aspsp": {"name": aspsp_name, "country": aspsp_country},
            "state": state,
            "redirect_url": redirect_url,
            "psu_type": "personal",
        }

        if valid_until:
            body["access"] = {"valid_until": valid_until}

        return await self._make_request("POST", "/auth", json=body)

    async def create_session(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for a session."""
        return await self._make_request("POST", "/sessions", json={"code": code})

    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session details."""
        return await self._make_request("GET", f"/sessions/{session_id}")

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
