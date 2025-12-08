"""Account enrichment processor for adding currency, logos, and metadata."""

from typing import Any, Dict

from loguru import logger

from leggen.services.gocardless_service import GoCardlessService


class AccountEnricher:
    """Enriches account details with currency and institution information."""

    def __init__(self):
        self.gocardless = GoCardlessService()

    async def enrich_account_details(
        self,
        account_details: Dict[str, Any],
        balances: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Enrich account details with currency from balances and institution logo.

        Args:
            account_details: Raw account details from GoCardless
            balances: Balance data containing currency information

        Returns:
            Enriched account details with currency and logo added
        """
        enriched_account = account_details.copy()

        # Extract currency from first balance
        currency = self._extract_currency_from_balances(balances)
        if currency:
            enriched_account["currency"] = currency

        # Fetch and add institution logo
        institution_id = enriched_account.get("institution_id")
        if institution_id:
            logo = await self._fetch_institution_logo(institution_id)
            if logo:
                enriched_account["logo"] = logo

        return enriched_account

    def _extract_currency_from_balances(self, balances: Dict[str, Any]) -> str | None:
        """Extract currency from the first balance in the balances data."""
        balances_list = balances.get("balances", [])
        if not balances_list:
            return None

        first_balance = balances_list[0]
        balance_amount = first_balance.get("balanceAmount", {})
        return balance_amount.get("currency")

    async def _fetch_institution_logo(self, institution_id: str) -> str | None:
        """Fetch institution logo from GoCardless API."""
        try:
            institution_details = await self.gocardless.get_institution_details(
                institution_id
            )
            logo = institution_details.get("logo", "")
            if logo:
                logger.info(f"Fetched logo for institution {institution_id}: {logo}")
            return logo
        except Exception as e:
            logger.warning(
                f"Failed to fetch institution details for {institution_id}: {e}"
            )
            return None
