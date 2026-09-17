"""Tests for the category rule engine."""

import pytest

from leggen.errors import InvalidRuleScriptError
from leggen.repositories import (
    CategoryRepository,
    CategoryRuleRepository,
    TransactionRepository,
)
from leggen.repositories.db import get_db_connection
from leggen.services.rules import CategoryRuleEngine


def _category(name: str) -> int:
    return next(
        c for c in CategoryRepository().get_all_categories() if c["name"] == name
    )["id"]


def _seed_transactions(rows: list[tuple[str, str, float]]) -> None:
    """(transaction_id, description, amount) on one account."""
    TransactionRepository().persist(
        "acc-1",
        [
            {
                "transactionId": txn_id,
                "internalTransactionId": f"int-{txn_id}",
                "institutionId": "TEST_BANK",
                "iban": "PT1",
                "accountId": "acc-1",
                "transactionDate": "2025-09-05T10:00:00",
                "description": description,
                "transactionValue": amount,
                "transactionCurrency": "EUR",
                "transactionStatus": "booked",
                "rawTransaction": {},
            }
            for txn_id, description, amount in rows
        ],
    )


def _assignments() -> dict[str, tuple[int, str, int | None]]:
    with get_db_connection(row_factory=True) as conn:
        rows = conn.execute(
            "SELECT transactionId, categoryId, source, ruleId FROM transaction_categories"
        ).fetchall()
        return {
            r["transactionId"]: (r["categoryId"], r["source"], r["ruleId"])
            for r in rows
        }


@pytest.fixture
def seeded(mock_db_path):
    _seed_transactions(
        [
            ("t-pingo", "COMPRA PINGO DOCE", -30.0),
            ("t-uber", "UBER EATS", -15.0),
            ("t-salary", "ACME LDA SALARIO", 2000.0),
            ("t-other", "SOMETHING ELSE", -5.0),
        ]
    )
    rules = CategoryRuleRepository()
    groceries = rules.create_rule(
        "Groceries",
        _category("Groceries"),
        'return contains(tx.description, "pingo")',
        priority=10,
    )
    dining = rules.create_rule(
        "Dining",
        _category("Dining"),
        'return contains(tx.description, "uber")',
        priority=20,
    )
    return {"groceries": groceries, "dining": dining}


@pytest.mark.unit
class TestRun:
    def test_first_matching_rule_wins_by_priority(self, seeded):
        rules = CategoryRuleRepository()
        # A broader rule at a lower priority must not steal the match.
        rules.create_rule(
            "Catch-all", _category("Shopping"), "return tx.is_expense", priority=999
        )

        result = CategoryRuleEngine().run()

        assert result.assigned == 3
        assigned = _assignments()
        assert assigned["t-pingo"][0] == _category("Groceries")
        assert assigned["t-uber"][0] == _category("Dining")
        assert assigned["t-other"][0] == _category("Shopping")
        assert "t-salary" not in assigned
        assert all(source == "rule" for _, source, _ in assigned.values())

    def test_higher_priority_number_can_still_win_when_earlier_rules_miss(self, seeded):
        result = CategoryRuleEngine().run()

        assert _assignments()["t-uber"] == (
            _category("Dining"),
            "rule",
            seeded["dining"]["id"],
        )
        assert result.rules_evaluated == 2
        assert result.transactions_evaluated == 4

    def test_manual_assignments_are_never_touched(self, seeded):
        CategoryRepository().assign_category("acc-1", "t-pingo", _category("Dining"))

        CategoryRuleEngine().run()

        assert _assignments()["t-pingo"] == (_category("Dining"), "manual", None)

    def test_is_idempotent(self, seeded):
        engine = CategoryRuleEngine()
        engine.run()

        second = engine.run()

        assert second.assigned == 0
        assert second.cleared == 0
        assert second.changes == []

    def test_clears_assignments_no_rule_reproduces(self, seeded):
        engine = CategoryRuleEngine()
        engine.run()
        CategoryRuleRepository().update_rule(seeded["groceries"]["id"], is_active=False)

        result = engine.run()

        assert result.cleared == 1
        assert "t-pingo" not in _assignments()
        assert [c.action for c in result.changes] == ["clear"]
        assert result.changes[0].previous_category_id == _category("Groceries")

    def test_reassigns_when_the_winning_rule_changes(self, seeded):
        engine = CategoryRuleEngine()
        engine.run()
        # A new, earlier rule now claims the Pingo Doce transaction.
        shopping = CategoryRuleRepository().create_rule(
            "Shopping first",
            _category("Shopping"),
            'return contains(tx.description, "pingo")',
            priority=1,
        )

        result = engine.run()

        assert result.assigned == 1
        assert _assignments()["t-pingo"] == (
            _category("Shopping"),
            "rule",
            shopping["id"],
        )
        change = result.changes[0]
        assert change.action == "assign"
        assert change.previous_rule_id == seeded["groceries"]["id"]

    def test_dry_run_reports_without_writing(self, seeded):
        result = CategoryRuleEngine().run(dry_run=True)

        assert result.dry_run is True
        assert result.assigned == 2
        assert {c.transaction_id for c in result.changes} == {"t-pingo", "t-uber"}
        assert _assignments() == {}

    def test_keys_limit_the_pass(self, seeded):
        result = CategoryRuleEngine().run(keys=[("acc-1", "t-uber")])

        assert result.transactions_evaluated == 1
        assert set(_assignments()) == {"t-uber"}

    def test_exclusion_flag_is_applied(self, seeded):
        CategoryRuleRepository().update_rule(
            seeded["groceries"]["id"], exclude_from_stats=True
        )

        CategoryRuleEngine().run()

        with get_db_connection() as conn:
            flag = conn.execute(
                "SELECT exclude_from_stats FROM transaction_categories WHERE transactionId = 't-pingo'"
            ).fetchone()[0]
        assert flag == 1

    def test_a_rule_that_does_not_compile_is_skipped(self, seeded):
        broken = CategoryRuleRepository().create_rule(
            "Broken", _category("Shopping"), "if then", priority=1
        )

        result = CategoryRuleEngine().run()

        assert broken["id"] in result.skipped_rules
        assert "line 1" in result.skipped_rules[broken["id"]]
        assert result.rules_evaluated == 2
        assert result.assigned == 2  # the healthy rules still ran

    def test_runtime_errors_are_counted_not_fatal(self, seeded):
        faulty = CategoryRuleRepository().create_rule(
            "Faulty", _category("Shopping"), "return tx.raw.a.b == 1", priority=1
        )

        result = CategoryRuleEngine().run()

        report = result.errors[faulty["id"]]
        assert report.rule_name == "Faulty"
        assert report.count == 4  # every transaction
        assert len(report.samples) == 1  # identical messages collapse
        assert result.assigned == 2  # later rules still matched

    def test_no_rules_is_a_clean_no_op(self, mock_db_path):
        _seed_transactions([("t", "X", -1.0)])

        result = CategoryRuleEngine().run()

        assert result.rules_evaluated == 0
        assert result.assigned == 0
        assert _assignments() == {}


@pytest.mark.unit
class TestAuthoringHelpers:
    def test_test_script_against_one_transaction(self, seeded):
        outcome = CategoryRuleEngine().test_script(
            'log(tx.merchant) return contains(tx.description, "pingo")',
            "acc-1",
            "t-pingo",
        )

        assert outcome.matched is True
        assert outcome.logs == ["COMPRA PINGO DOCE"]

    def test_test_script_syntax_error(self, seeded):
        with pytest.raises(InvalidRuleScriptError):
            CategoryRuleEngine().test_script("if then", "acc-1", "t-pingo")

    def test_test_script_unknown_transaction(self, seeded):
        with pytest.raises(LookupError):
            CategoryRuleEngine().test_script("return true", "acc-1", "nope")

    def test_preview_includes_and_flags_manual_rows(self, seeded):
        CategoryRepository().assign_category("acc-1", "t-pingo", _category("Dining"))

        preview = CategoryRuleEngine().preview_script("return tx.is_expense")

        assert preview.evaluated == 4
        assert preview.matched == 3
        by_id = {m.transaction_id: m for m in preview.matches}
        assert by_id["t-pingo"].manual is True
        assert by_id["t-pingo"].category_name == "Dining"
        assert by_id["t-uber"].manual is False
        assert preview.errors == 0

    def test_preview_counts_errors(self, seeded):
        preview = CategoryRuleEngine().preview_script("return tx.raw.a.b == 1")

        assert preview.matched == 0
        assert preview.errors == 4
        assert len(preview.error_samples) == 1
