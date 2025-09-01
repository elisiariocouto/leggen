import asyncio
import httpx
from typing import Dict, Any, List, Optional

from loguru import logger

from leggend.config import config


class GoCardlessService:
    def __init__(self):
        self.config = config.gocardless_config
        self.base_url = self.config.get("url", "https://bankaccountdata.gocardless.com/api/v2")
        self.headers = self._get_auth_headers()

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for GoCardless API"""
        # This would implement the token-based auth similar to leggen.utils.auth
        # For now, placeholder implementation
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json"
        }

    def _get_token(self) -> str:
        """Get access token for GoCardless API"""
        # Implementation would be similar to leggen.utils.auth.get_token
        # This is a simplified placeholder
        return "placeholder_token"

    async def get_institutions(self, country: str = "PT") -> List[Dict[str, Any]]:
        """Get available bank institutions for a country"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/institutions/",
                headers=self.headers,
                params={"country": country}
            )
            response.raise_for_status()
            return response.json()

    async def create_requisition(self, institution_id: str, redirect_url: str) -> Dict[str, Any]:
        """Create a bank connection requisition"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/requisitions/",
                headers=self.headers,
                json={
                    "institution_id": institution_id,
                    "redirect": redirect_url
                }
            )
            response.raise_for_status()
            return response.json()

    async def get_requisitions(self) -> Dict[str, Any]:
        """Get all requisitions"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/requisitions/",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_account_details(self, account_id: str) -> Dict[str, Any]:
        """Get account details"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/accounts/{account_id}/",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_account_balances(self, account_id: str) -> Dict[str, Any]:
        """Get account balances"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/accounts/{account_id}/balances/",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_account_transactions(self, account_id: str) -> Dict[str, Any]:
        """Get account transactions"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/accounts/{account_id}/transactions/",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()