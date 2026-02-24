"""Account enrichment processor for adding currency, logos, and metadata."""

from typing import Any, Dict

from loguru import logger

from leggen.services.enablebanking_service import EnableBankingService


class AccountEnricher:
    """Enriches account details with currency and institution information."""

    def __init__(self):
        self.enablebanking = EnableBankingService()

    async def enrich_account_details(
        self,
        account_details: Dict[str, Any],
        balances: Dict[str, Any],
        aspsp_country: str | None = None,
    ) -> Dict[str, Any]:
        """
        Enrich account details with currency from balances and institution logo.

        Args:
            account_details: Raw account details from EnableBanking
            balances: Balance data containing currency information
            aspsp_country: Country code for looking up institution logo

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
        if institution_id and aspsp_country:
            logo = await self._fetch_institution_logo(institution_id, aspsp_country)
            if logo:
                enriched_account["logo"] = logo

        return enriched_account

    def _extract_currency_from_balances(self, balances: Dict[str, Any]) -> str | None:
        """Extract currency from the first balance in the balances data."""
        balances_list = balances.get("balances", [])
        if not balances_list:
            return None

        first_balance = balances_list[0]
        balance_amount = first_balance.get("balance_amount", {})
        return balance_amount.get("currency")

    async def _fetch_institution_logo(
        self, aspsp_name: str, country: str
    ) -> str | None:
        """Fetch institution logo from EnableBanking API."""
        try:
            aspsps = await self.enablebanking.get_aspsps(country)
            for aspsp in aspsps:
                if aspsp.get("name") == aspsp_name:
                    logo = aspsp.get("logo", "")
                    if logo:
                        logger.info(f"Fetched logo for ASPSP {aspsp_name}: {logo}")
                    return logo
            return None
        except Exception as e:
            logger.warning(f"Failed to fetch institution details for {aspsp_name}: {e}")
            return None
