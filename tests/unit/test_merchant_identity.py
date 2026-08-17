"""Tests for merchant/counterparty identification.

The example strings here are shapes taken from real bank feeds (Revolut and
Portuguese banks), because the generated sample database is far cleaner than
real remittance information and would not exercise the normalization at all.
"""

from leggen.services.data_processors import (
    counterparty_name,
    merchant_identity,
    normalize_merchant,
)


class TestCounterpartyName:
    """EnableBanking nests counterparty names one level down."""

    def test_reads_nested_name(self):
        raw = {"creditor": {"name": "Continente Bom Dia"}}
        assert counterparty_name(raw, "creditor") == "Continente Bom Dia"

    def test_reads_debtor_side(self):
        raw = {"debtor": {"name": "ACME Payroll"}}
        assert counterparty_name(raw, "debtor") == "ACME Payroll"

    def test_accepts_flat_fallback(self):
        """The flat camelCase form is still honored if a provider sends it."""
        assert counterparty_name({"creditorName": "Tesco"}, "creditor") == "Tesco"

    def test_missing_returns_empty(self):
        assert counterparty_name({}, "creditor") == ""
        assert counterparty_name({"creditor": None}, "creditor") == ""
        assert counterparty_name({"creditor": {}}, "creditor") == ""


class TestNormalizeMerchant:
    """Strip the reference noise banks wrap around a merchant name."""

    def test_strips_terminal_and_reference_numbers(self):
        assert normalize_merchant("COMPRA 3007 Revolut 3600 Dublin IE") == (
            "COMPRA Revolut Dublin IE"
        )

    def test_strips_dates(self):
        assert normalize_merchant("TESCO STORES 12/03") == "TESCO STORES"

    def test_collapses_punctuation_and_whitespace(self):
        """Display casing is preserved; only the grouping key casefolds."""
        assert normalize_merchant("Uber * Eats") == "Uber Eats"
        assert normalize_merchant("Uber   *eats") == "Uber eats"

    def test_strips_pending_marker(self):
        assert normalize_merchant("Uber * Eats Pending") == normalize_merchant(
            "Uber * Eats"
        )

    def test_empty_input_is_labeled(self):
        assert normalize_merchant("") == "Unknown"
        assert normalize_merchant(None) == "Unknown"

    def test_all_noise_falls_back_to_original(self):
        """A description of pure noise keeps something displayable."""
        assert normalize_merchant("12345678") == "12345678"


class TestMerchantIdentity:
    """Grouping key vs display label."""

    def test_prefers_structured_name_over_description(self):
        raw = {"creditor": {"name": "Continente Bom Dia"}}
        key, display = merchant_identity(raw, "PAG BXVAL- 3007 NOISE", is_expense=True)
        assert display == "Continente Bom Dia"
        assert key == "continente bom dia"

    def test_falls_back_to_description(self):
        """Real data populates creditor.name on only ~3.5% of rows."""
        key, display = merchant_identity({}, "Ui... Que Larica", is_expense=True)
        assert display == "Ui Que Larica"
        assert key == "ui que larica"

    def test_directional_prefix_ignored_in_key(self):
        """ "FLEXIBLE CASH FUNDS" and "To Flexible Cash Funds" are one merchant."""
        key_a, _ = merchant_identity({}, "FLEXIBLE CASH FUNDS", is_expense=True)
        key_b, _ = merchant_identity({}, "To Flexible Cash Funds", is_expense=True)
        assert key_a == key_b

    def test_reference_noise_does_not_split_a_merchant(self):
        key_a, _ = merchant_identity({}, "Uber * Eats Pending", is_expense=True)
        key_b, _ = merchant_identity({}, "Uber   *eats", is_expense=True)
        assert key_a == key_b

    def test_income_uses_debtor_side(self):
        raw = {"debtor": {"name": "ACME Payroll"}}
        _, display = merchant_identity(raw, "SALARY", is_expense=False)
        assert display == "ACME Payroll"

    def test_falls_back_to_populated_side(self):
        """Some providers only fill the side opposite the flow direction."""
        raw = {"creditor": {"name": "Landlord"}}
        _, display = merchant_identity(raw, "RENT", is_expense=False)
        assert display == "Landlord"

    def test_case_insensitive_grouping(self):
        key_a, _ = merchant_identity({}, "APPLE.COM", is_expense=True)
        key_b, _ = merchant_identity({}, "apple.com", is_expense=True)
        assert key_a == key_b
