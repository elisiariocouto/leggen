import os
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import requests

from leggen.utils.text import error


class LeggenAPIClient:
    """Client for communicating with the leggen FastAPI service"""

    base_url: str

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (
            base_url
            or os.environ.get("LEGGEN_API_URL", "http://localhost:8000")
            or "http://localhost:8000"
        )
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to the API"""
        url = urljoin(self.base_url, endpoint)

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            error("Could not connect to leggen server. Is it running?")
            error(f"Trying to connect to: {self.base_url}")
            raise
        except requests.exceptions.HTTPError as e:
            error(f"API request failed: {e}")
            if response.text:
                try:
                    error_data = response.json()
                    error(f"Error details: {error_data.get('detail', 'Unknown error')}")
                except Exception:
                    error(f"Response: {response.text}")
            raise
        except Exception as e:
            error(f"Unexpected error: {e}")
            raise

    def health_check(self) -> bool:
        """Check if the leggen server is healthy"""
        try:
            response = self._make_request("GET", "/health")
            return response.get("status") == "healthy"
        except Exception:
            return False

    # Bank endpoints
    def get_institutions(self, country: str = "PT") -> List[Dict[str, Any]]:
        """Get bank institutions for a country"""
        response = self._make_request(
            "GET", "/api/v1/banks/institutions", params={"country": country}
        )
        return response.get("data", [])

    def connect_to_bank(
        self, institution_id: str, redirect_url: str = "http://localhost:8000/"
    ) -> Dict[str, Any]:
        """Connect to a bank"""
        response = self._make_request(
            "POST",
            "/api/v1/banks/connect",
            json={"institution_id": institution_id, "redirect_url": redirect_url},
        )
        return response.get("data", {})

    def get_bank_status(self) -> List[Dict[str, Any]]:
        """Get bank connection status"""
        response = self._make_request("GET", "/api/v1/banks/status")
        return response.get("data", [])

    def get_supported_countries(self) -> List[Dict[str, Any]]:
        """Get supported countries"""
        response = self._make_request("GET", "/api/v1/banks/countries")
        return response.get("data", [])

    # Account endpoints
    def get_accounts(self) -> List[Dict[str, Any]]:
        """Get all accounts"""
        response = self._make_request("GET", "/api/v1/accounts")
        return response.get("data", [])

    def get_account_details(self, account_id: str) -> Dict[str, Any]:
        """Get account details"""
        response = self._make_request("GET", f"/api/v1/accounts/{account_id}")
        return response.get("data", {})

    def get_account_balances(self, account_id: str) -> List[Dict[str, Any]]:
        """Get account balances"""
        response = self._make_request("GET", f"/api/v1/accounts/{account_id}/balances")
        return response.get("data", [])

    def get_account_transactions(
        self, account_id: str, limit: int = 100, summary_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Get account transactions"""
        response = self._make_request(
            "GET",
            f"/api/v1/accounts/{account_id}/transactions",
            params={"limit": limit, "summary_only": summary_only},
        )
        return response.get("data", [])

    # Transaction endpoints
    def get_all_transactions(
        self, limit: int = 100, summary_only: bool = True, **filters
    ) -> List[Dict[str, Any]]:
        """Get all transactions with optional filters"""
        params = {"limit": limit, "summary_only": summary_only}
        params.update(filters)

        response = self._make_request("GET", "/api/v1/transactions", params=params)
        return response.get("data", [])

    def get_transaction_stats(
        self, days: int = 30, account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get transaction statistics"""
        params: Dict[str, Union[int, str]] = {"days": days}
        if account_id:
            params["account_id"] = account_id

        response = self._make_request(
            "GET", "/api/v1/transactions/stats", params=params
        )
        return response.get("data", {})

    # Sync endpoints
    def get_sync_status(self) -> Dict[str, Any]:
        """Get sync status"""
        response = self._make_request("GET", "/api/v1/sync/status")
        return response.get("data", {})

    def trigger_sync(
        self, account_ids: Optional[List[str]] = None, force: bool = False
    ) -> Dict[str, Any]:
        """Trigger a sync"""
        data: Dict[str, Union[bool, List[str]]] = {"force": force}
        if account_ids:
            data["account_ids"] = account_ids

        response = self._make_request("POST", "/api/v1/sync", json=data)
        return response.get("data", {})

    def sync_now(
        self, account_ids: Optional[List[str]] = None, force: bool = False
    ) -> Dict[str, Any]:
        """Run sync synchronously"""
        data: Dict[str, Union[bool, List[str]]] = {"force": force}
        if account_ids:
            data["account_ids"] = account_ids

        response = self._make_request("POST", "/api/v1/sync/now", json=data)
        return response.get("data", {})

    def get_scheduler_config(self) -> Dict[str, Any]:
        """Get scheduler configuration"""
        response = self._make_request("GET", "/api/v1/sync/scheduler")
        return response.get("data", {})

    def update_scheduler_config(
        self,
        enabled: bool = True,
        hour: int = 3,
        minute: int = 0,
        cron: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update scheduler configuration"""
        data: Dict[str, Union[bool, int, str]] = {
            "enabled": enabled,
            "hour": hour,
            "minute": minute,
        }
        if cron:
            data["cron"] = cron

        response = self._make_request("PUT", "/api/v1/sync/scheduler", json=data)
        return response.get("data", {})
