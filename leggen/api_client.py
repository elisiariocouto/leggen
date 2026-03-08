import os
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse

import requests
import urllib3

from leggen.utils.text import error


class LeggenAPIClient:
    """Client for communicating with the leggen FastAPI service"""

    base_url: str

    def __init__(self, base_url: Optional[str] = None, verify_ssl: bool = True):
        raw_url = (
            base_url
            or os.environ.get("LEGGEN_API_URL", "http://localhost:8000")
            or "http://localhost:8000"
        )
        # Ensure base_url includes /api/v1 path if not already present
        parsed = urlparse(raw_url)
        if not parsed.path or parsed.path == "/":
            # No path or just root, add /api/v1
            self.base_url = f"{raw_url.rstrip('/')}/api/v1"
        elif not parsed.path.startswith("/api/v1"):
            # Has a path but not /api/v1, add it
            self.base_url = f"{raw_url.rstrip('/')}/api/v1"
        else:
            # Already has /api/v1 path
            self.base_url = raw_url.rstrip("/")
        self.verify_ssl = verify_ssl
        if not verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make HTTP request to the API"""
        # Construct URL by joining base_url with endpoint
        # Handle both relative endpoints (starting with /) and paths
        if endpoint.startswith("/"):
            # Absolute endpoint path - append to base_url
            url = f"{self.base_url}{endpoint}"
        else:
            # Relative endpoint, use urljoin
            url = urljoin(f"{self.base_url}/", endpoint)

        try:
            response = self.session.request(
                method, url, verify=self.verify_ssl, **kwargs
            )
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
        """Get bank institutions (ASPSPs) for a country"""
        response = self._make_request(
            "GET", "/banks/institutions", params={"country": country}
        )
        return response

    def connect_to_bank(
        self,
        aspsp_name: str,
        aspsp_country: str,
        redirect_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Start bank authorization flow"""
        payload: Dict[str, Any] = {
            "aspsp_name": aspsp_name,
            "aspsp_country": aspsp_country,
        }
        if redirect_url:
            payload["redirect_url"] = redirect_url
        response = self._make_request("POST", "/banks/connect", json=payload)
        return response

    def exchange_auth_code(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for a session"""
        response = self._make_request("POST", "/banks/callback", json={"code": code})
        return response

    def get_bank_status(self) -> List[Dict[str, Any]]:
        """Get bank connection status"""
        response = self._make_request("GET", "/banks/status")
        return response

    def delete_bank_connection(self, session_id: str) -> Dict[str, Any]:
        """Delete a bank connection session"""
        return self._make_request("DELETE", f"/banks/connections/{session_id}")

    def get_supported_countries(self) -> List[Dict[str, Any]]:
        """Get supported countries"""
        response = self._make_request("GET", "/banks/countries")
        return response

    # Account endpoints
    def get_accounts(self) -> List[Dict[str, Any]]:
        """Get all accounts"""
        response = self._make_request("GET", "/accounts")
        return response

    def delete_account(
        self, account_id: str, delete_data: bool = True
    ) -> Dict[str, Any]:
        """Delete a bank account and optionally its associated data"""
        return self._make_request(
            "DELETE",
            f"/accounts/{account_id}",
            params={"delete_data": str(delete_data).lower()},
        )

    # Transaction endpoints
    def get_all_transactions(
        self, limit: int = 100, summary_only: bool = True, **filters
    ) -> List[Dict[str, Any]]:
        """Get all transactions with optional filters"""
        params = {"per_page": limit, "summary_only": summary_only}
        params.update(filters)

        response = self._make_request("GET", "/transactions", params=params)
        return response.get("data", [])

    def get_transaction_stats(
        self, days: int = 30, account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get transaction statistics"""
        params: Dict[str, Union[int, str]] = {"days": days}
        if account_id:
            params["account_id"] = account_id

        response = self._make_request("GET", "/transactions/stats", params=params)
        return response

    # Sync endpoints
    def trigger_sync(
        self, account_ids: Optional[List[str]] = None, full_sync: bool = False
    ) -> Dict[str, Any]:
        """Trigger a synchronous sync"""
        data: Dict[str, Union[bool, List[str]]] = {"full_sync": full_sync}
        if account_ids:
            data["account_ids"] = account_ids

        response = self._make_request("POST", "/sync", json=data)
        return response
