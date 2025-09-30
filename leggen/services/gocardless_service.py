import json
from pathlib import Path
from typing import Any, Dict

import httpx
from loguru import logger

from leggen.utils.config import config
from leggen.utils.paths import path_manager


def _log_rate_limits(response, method, url):
    """Log GoCardless API rate limit headers"""
    limit = response.headers.get("http_x_ratelimit_limit")
    remaining = response.headers.get("http_x_ratelimit_remaining")
    reset = response.headers.get("http_x_ratelimit_reset")

    account_limit = response.headers.get("http_x_ratelimit_account_success_limit")
    account_remaining = response.headers.get(
        "http_x_ratelimit_account_success_remaining"
    )
    account_reset = response.headers.get("http_x_ratelimit_account_success_reset")

    logger.debug(
        f"{method} {url} Limit/Remaining/Reset (Global: {limit}/{remaining}/{reset}s) (Account: {account_limit}/{account_remaining}/{account_reset}s)"
    )


class GoCardlessService:
    def __init__(self):
        self.config = config.gocardless_config
        self.base_url = self.config.get(
            "url", "https://bankaccountdata.gocardless.com/api/v2"
        )
        self._token = None

    async def _make_authenticated_request(
        self, method: str, url: str, **kwargs
    ) -> Dict[str, Any]:
        """Make authenticated request with automatic token refresh on 401"""
        headers = await self._get_auth_headers()

        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, headers=headers, **kwargs)
            _log_rate_limits(response, method, url)

            # If we get 401, clear token cache and retry once
            if response.status_code == 401:
                logger.warning("Got 401, clearing token cache and retrying")
                self._token = None
                headers = await self._get_auth_headers()
                response = await client.request(method, url, headers=headers, **kwargs)
                _log_rate_limits(response, method, url)

            response.raise_for_status()
            return response.json()

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
                            _log_rate_limits(
                                response, "POST", f"{self.base_url}/token/refresh/"
                            )
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
                _log_rate_limits(response, "POST", f"{self.base_url}/token/new/")
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

    async def get_institutions(self, country: str = "PT") -> Dict[str, Any]:
        """Get available bank institutions for a country"""
        return await self._make_authenticated_request(
            "GET", f"{self.base_url}/institutions/", params={"country": country}
        )

    async def create_requisition(
        self, institution_id: str, redirect_url: str
    ) -> Dict[str, Any]:
        """Create a bank connection requisition"""
        return await self._make_authenticated_request(
            "POST",
            f"{self.base_url}/requisitions/",
            json={"institution_id": institution_id, "redirect": redirect_url},
        )

    async def get_requisitions(self) -> Dict[str, Any]:
        """Get all requisitions"""
        return await self._make_authenticated_request(
            "GET", f"{self.base_url}/requisitions/"
        )

    async def delete_requisition(self, requisition_id: str) -> Dict[str, Any]:
        """Delete a requisition"""
        return await self._make_authenticated_request(
            "DELETE", f"{self.base_url}/requisitions/{requisition_id}/"
        )

    async def get_account_details(self, account_id: str) -> Dict[str, Any]:
        """Get account details"""
        return await self._make_authenticated_request(
            "GET", f"{self.base_url}/accounts/{account_id}/"
        )

    async def get_account_balances(self, account_id: str) -> Dict[str, Any]:
        """Get account balances"""
        return await self._make_authenticated_request(
            "GET", f"{self.base_url}/accounts/{account_id}/balances/"
        )

    async def get_account_transactions(self, account_id: str) -> Dict[str, Any]:
        """Get account transactions"""
        return await self._make_authenticated_request(
            "GET", f"{self.base_url}/accounts/{account_id}/transactions/"
        )

    async def get_institution_details(self, institution_id: str) -> Dict[str, Any]:
        """Get institution details by ID"""
        return await self._make_authenticated_request(
            "GET", f"{self.base_url}/institutions/{institution_id}/"
        )
