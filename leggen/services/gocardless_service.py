import json
from pathlib import Path
from typing import Any, Dict, List

import httpx
from loguru import logger

from leggen.utils.config import config
from leggen.utils.paths import path_manager


def _log_rate_limits(response):
    """Log GoCardless API rate limit headers"""
    limit = response.headers.get("X-RateLimit-Limit")
    remaining = response.headers.get("X-RateLimit-Remaining")
    reset = response.headers.get("X-RateLimit-Reset")
    account_success_reset = response.headers.get("X-RateLimit-Account-Success-Reset")

    if limit or remaining or reset or account_success_reset:
        logger.info(
            f"GoCardless rate limits - Limit: {limit}, Remaining: {remaining}, Reset: {reset}s, Account Success Reset: {account_success_reset}"
        )


class GoCardlessService:
    def __init__(self):
        self.config = config.gocardless_config
        self.base_url = self.config.get(
            "url", "https://bankaccountdata.gocardless.com/api/v2"
        )
        self._token = None

    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for GoCardless API"""
        token = await self._get_token()
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async def _get_token(self) -> str:
        """Get access token for GoCardless API"""
        if self._token:
            return self._token

        # Use path manager for auth file
        auth_file = path_manager.get_auth_file_path()

        if auth_file.exists():
            try:
                with open(auth_file, "r") as f:
                    auth = json.load(f)

                if auth.get("access"):
                    # Try to refresh the token
                    async with httpx.AsyncClient() as client:
                        try:
                            response = await client.post(
                                f"{self.base_url}/token/refresh/",
                                json={"refresh": auth["refresh"]},
                            )
                            _log_rate_limits(response)
                            response.raise_for_status()
                            auth.update(response.json())
                            self._save_auth(auth)
                            self._token = auth["access"]
                            return self._token
                        except httpx.HTTPStatusError:
                            logger.warning("Token refresh failed, creating new token")
                            return await self._create_token()
                else:
                    return await self._create_token()
            except Exception as e:
                logger.error(f"Error reading auth file: {e}")
                return await self._create_token()
        else:
            return await self._create_token()

    async def _create_token(self) -> str:
        """Create a new GoCardless access token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/token/new/",
                    json={
                        "secret_id": self.config["key"],
                        "secret_key": self.config["secret"],
                    },
                )
                _log_rate_limits(response)
                response.raise_for_status()
                auth = response.json()
                self._save_auth(auth)
                self._token = auth["access"]
                return self._token
        except Exception as e:
            logger.error(f"Failed to create GoCardless token: {e}")
            raise

    def _save_auth(self, auth_data: dict):
        """Save authentication data to file"""
        auth_file = Path.home() / ".config" / "leggen" / "auth.json"
        auth_file.parent.mkdir(parents=True, exist_ok=True)

        with open(auth_file, "w") as f:
            json.dump(auth_data, f)

    async def get_institutions(self, country: str = "PT") -> List[Dict[str, Any]]:
        """Get available bank institutions for a country"""
        headers = await self._get_auth_headers()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/institutions/",
                headers=headers,
                params={"country": country},
            )
            _log_rate_limits(response)
            response.raise_for_status()
            return response.json()

    async def create_requisition(
        self, institution_id: str, redirect_url: str
    ) -> Dict[str, Any]:
        """Create a bank connection requisition"""
        headers = await self._get_auth_headers()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/requisitions/",
                headers=headers,
                json={"institution_id": institution_id, "redirect": redirect_url},
            )
            _log_rate_limits(response)
            response.raise_for_status()
            return response.json()

    async def get_requisitions(self) -> Dict[str, Any]:
        """Get all requisitions"""
        headers = await self._get_auth_headers()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/requisitions/", headers=headers
            )
            _log_rate_limits(response)
            response.raise_for_status()
            return response.json()

    async def get_account_details(self, account_id: str) -> Dict[str, Any]:
        """Get account details"""
        headers = await self._get_auth_headers()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/accounts/{account_id}/", headers=headers
            )
            _log_rate_limits(response)
            response.raise_for_status()
            return response.json()

    async def get_account_balances(self, account_id: str) -> Dict[str, Any]:
        """Get account balances"""
        headers = await self._get_auth_headers()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/accounts/{account_id}/balances/", headers=headers
            )
            _log_rate_limits(response)
            response.raise_for_status()
            return response.json()

    async def get_account_transactions(self, account_id: str) -> Dict[str, Any]:
        """Get account transactions"""
        headers = await self._get_auth_headers()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/accounts/{account_id}/transactions/", headers=headers
            )
            _log_rate_limits(response)
            response.raise_for_status()
            return response.json()
