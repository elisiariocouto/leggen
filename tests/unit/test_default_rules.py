"""Tests for the builtin category rules and their seeding."""

import pytest

from leggen.repositories import (
    AccountRepository,
    CategoryRepository,
    CategoryRuleRepository,
    TransactionRepository,
)
from leggen.repositories.db import get_db_connection
from leggen.services.rules import (
    DEFAULT_CATEGORY_RULES,
    CategoryRuleEngine,
    seed_default_category_rules,
    validate_script,
)

# Descriptions the sample generator uses, with the category each should get.
# The builtin rules are judged against these: a fresh install with sample
# data should come out categorized, and nothing should be mislabeled.
GROUND_TRUTH = {
    "TESCO": "Groceries",
    "SAINSBURY'S": "Groceries",
    "LIDL": "Groceries",
    "ALDI": "Groceries",
    "WALMART": "Groceries",
    "CARREFOUR": "Groceries",
    "STARBUCKS": "Dining",
    "COSTA COFFEE": "Dining",
    "PRET A MANGER": "Dining",
    "LOCAL CAFE": "Dining",
    "PIZZA HUT": "Dining",
    "MCDONALD'S": "Dining",
    "BURGER KING": "Dining",
    "LOCAL RESTAURANT": "Dining",
    "UBER EATS": "Dining",
    "BP": "Transport",
    "SHELL": "Transport",
    "ESSO": "Transport",
    "GALP": "Transport",
    "PETROBRAS": "Transport",
    "UBER": "Transport",
    "GALP ENERGIA": "Utilities",
    "AMAZON": "Shopping",
    "EBAY": "Shopping",
    "ZALANDO": "Shopping",
    "ASOS": "Shopping",
    "APPLE": "Shopping",
    "APPLE MUSIC": "Subscriptions",
    "NETFLIX": "Subscriptions",
    "ATM WITHDRAWAL": "Cash",
    "CASH WITHDRAWAL": "Cash",
    "SAVINGS TRANSFER": "Transfer",
    "INVESTMENT TRANSFER": "Transfer",
    "TRANSFER TO CHECKING": "Inter-account",
    "TRANSFER FROM SAVINGS": "Inter-account",
    "INTERNAL TRANSFER": "Inter-account",
}
INCOME_GROUND_TRUTH = {
    "MONTHLY SALARY": "Salary",
    "PAYROLL DEPOSIT": "Salary",
    "SALARY PAYMENT": "Salary",
}
# Must stay uncategorized: generic words a sloppy rule would catch.
NEGATIVES = [
    "BPI PRESTACAO",
    "MAXIMUS LDA",
    "DIALOGUE CONSULTING",
    "SHELLEY BOOKS",
    "BOM DIA PADEIRO",  # "dia" is a word, not a supermarket
    "5ASEC JUMBO MAIA",  # a laundry in a mall
]


def _categories() -> dict[int, str]:
    return {c["id"]: c["name"] for c in CategoryRepository().get_all_categories()}


def _seed_rows(rows: list[tuple[str, str, float, dict]]) -> None:
    TransactionRepository().persist(
        "acc-1",
        [
            {
                "transactionId": txn_id,
                "internalTransactionId": f"int-{txn_id}",
                "institutionId": "TEST_BANK",
                "iban": "PT50000201231234567890154",
                "accountId": "acc-1",
                "transactionDate": "2025-09-05T10:00:00",
                "description": description,
                "transactionValue": amount,
                "transactionCurrency": "EUR",
                "transactionStatus": "booked",
                "rawTransaction": raw,
            }
            for txn_id, description, amount, raw in rows
        ],
    )


def _assigned() -> dict[str, str]:
    names = _categories()
    with get_db_connection(row_factory=True) as conn:
        rows = conn.execute(
            "SELECT transactionId, categoryId FROM transaction_categories"
        ).fetchall()
        return {r["transactionId"]: names[r["categoryId"]] for r in rows}


@pytest.mark.unit
class TestSeeding:
    def test_seeds_every_rule_once(self, mock_db_path):
        assert seed_default_category_rules() == len(DEFAULT_CATEGORY_RULES)
        assert seed_default_category_rules() == 0

        rules = CategoryRuleRepository().get_all_rules()
        assert len(rules) == len(DEFAULT_CATEGORY_RULES)
        assert all(r["is_default"] and r["is_active"] for r in rules)
        assert [r["priority"] for r in rules] == sorted(r["priority"] for r in rules)

    def test_does_not_reseed_after_the_user_deletes_them(self, mock_db_path):
        seed_default_category_rules()
        repo = CategoryRuleRepository()
        for rule in repo.get_all_rules():
            repo.delete_rule(rule["id"])

        assert seed_default_category_rules() == 0
        assert repo.get_all_rules() == []

    def test_does_not_seed_over_user_rules(self, mock_db_path):
        groceries = next(
            c
            for c in CategoryRepository().get_all_categories()
            if c["name"] == "Groceries"
        )
        CategoryRuleRepository().create_rule("mine", groceries["id"], "return false")

        assert seed_default_category_rules() == 0

    def test_every_script_compiles(self):
        for rule in DEFAULT_CATEGORY_RULES:
            assert validate_script(rule["lua_script"]) is None, rule["name"]

    def test_names_are_unique_and_categories_exist(self, mock_db_path):
        names = [r["name"] for r in DEFAULT_CATEGORY_RULES]
        assert len(set(names)) == len(names)
        existing = set(_categories().values())
        assert {r["category"] for r in DEFAULT_CATEGORY_RULES} <= existing


@pytest.mark.unit
class TestPrecision:
    def test_ground_truth(self, mock_db_path):
        seed_default_category_rules()
        rows = [
            (f"e-{i}", description, -25.0, {})
            for i, description in enumerate(GROUND_TRUTH)
        ]
        rows += [
            (f"i-{i}", description, 2500.0, {})
            for i, description in enumerate(INCOME_GROUND_TRUTH)
        ]
        rows += [
            (f"n-{i}", description, -25.0, {})
            for i, description in enumerate(NEGATIVES)
        ]
        _seed_rows(rows)

        CategoryRuleEngine().run()

        assigned = _assigned()
        expected = {
            **{f"e-{i}": cat for i, cat in enumerate(GROUND_TRUTH.values())},
            **{f"i-{i}": cat for i, cat in enumerate(INCOME_GROUND_TRUTH.values())},
        }
        mismatches = {
            key: (assigned.get(key), want)
            for key, want in expected.items()
            if assigned.get(key) != want
        }
        assert mismatches == {}
        assert not any(key.startswith("n-") for key in assigned)

    def test_own_iban_transfer_is_inter_account(self, mock_db_path):
        seed_default_category_rules()
        for account_id, iban in (
            ("PT50000201231234567890154", "PT50000201231234567890154"),
            ("PT50003300004555555555555", "PT50 0033 0000 4555 5555 5555 5"),
        ):
            AccountRepository().persist(
                {
                    "id": account_id,
                    "institution_id": "TEST_BANK",
                    "status": "READY",
                    "iban": iban,
                    "created": "2025-01-01T00:00:00Z",
                }
            )
        _seed_rows(
            [
                (
                    "own",
                    "TRF SEPA",
                    -300.0,
                    {"creditor_account": {"iban": "PT50003300004555555555555"}},
                ),
                (
                    "other",
                    "TRF SEPA",
                    -300.0,
                    {"creditor_account": {"iban": "DE89370400440532013000"}},
                ),
                # Banks put the user's own account on the debtor side of every
                # expense; that must never read as a transfer to oneself.
                (
                    "fee",
                    "MANUTENCAO DE CONTA",
                    -5.0,
                    {
                        "debtor_account": {"iban": "PT50000201231234567890154"},
                        "creditor_account": {"iban": "PT50001000001111111111111"},
                    },
                ),
                (
                    "mbway",
                    "TRF MB WAY P  SOMEONE",
                    -20.0,
                    {"debtor_account": {"iban": "PT50000201231234567890154"}},
                ),
                # Income from one of the user's other accounts is a transfer.
                (
                    "incoming",
                    "TRF",
                    300.0,
                    {
                        "debtor_account": {"iban": "PT50003300004555555555555"},
                        "creditor_account": {"iban": "PT50000201231234567890154"},
                    },
                ),
            ]
        )

        CategoryRuleEngine().run()

        assert _assigned() == {"own": "Inter-account", "incoming": "Inter-account"}
