"""Tests for the category rule repository."""

import sqlite3

import pytest

from leggen.errors import CategoryRuleExistsError
from leggen.repositories import (
    CategoryRepository,
    CategoryRuleRepository,
    TransactionRepository,
)
from leggen.repositories.db import get_db_connection
from tests.conftest import persist_transactions


def _category_id(name: str = "Groceries") -> int:
    return next(
        c for c in CategoryRepository().get_all_categories() if c["name"] == name
    )["id"]


def _assignment(account_id: str, transaction_id: str) -> dict | None:
    with get_db_connection(row_factory=True) as conn:
        row = conn.execute(
            """SELECT categoryId, source, ruleId, exclude_from_stats
               FROM transaction_categories WHERE accountId = ? AND transactionId = ?""",
            (account_id, transaction_id),
        ).fetchone()
        return dict(row) if row else None


@pytest.mark.unit
class TestRuleCrud:
    def test_create_and_read(self, mock_db_path):
        repo = CategoryRuleRepository()

        rule = repo.create_rule(
            name="Supermarkets",
            category_id=_category_id(),
            lua_script='return contains(tx.merchant, "pingo")',
            description="Big chains",
            priority=10,
        )

        assert rule["id"] > 0
        assert rule["is_active"] is True
        assert rule["is_default"] is False
        assert rule["exclude_from_stats"] is None
        assert repo.get_rule_by_id(rule["id"]) == rule
        assert repo.get_rule_by_name("Supermarkets") == rule

    def test_listed_in_evaluation_order(self, mock_db_path):
        repo = CategoryRuleRepository()
        cat = _category_id()
        repo.create_rule("later", cat, "return false", priority=200)
        repo.create_rule("first", cat, "return false", priority=10)
        repo.create_rule("also-ten", cat, "return false", priority=10)

        assert [r["name"] for r in repo.get_all_rules()] == [
            "first",
            "also-ten",
            "later",
        ]

    def test_active_only(self, mock_db_path):
        repo = CategoryRuleRepository()
        cat = _category_id()
        repo.create_rule("on", cat, "return false")
        repo.create_rule("off", cat, "return false", is_active=False)

        assert [r["name"] for r in repo.get_all_rules(active_only=True)] == ["on"]

    def test_duplicate_name_is_a_conflict(self, mock_db_path):
        repo = CategoryRuleRepository()
        repo.create_rule("dup", _category_id(), "return false")

        with pytest.raises(CategoryRuleExistsError):
            repo.create_rule("dup", _category_id(), "return true")

    def test_unknown_category_is_rejected(self, mock_db_path):
        """Foreign keys are on, so the database refuses the row itself."""
        repo = CategoryRuleRepository()

        with pytest.raises(sqlite3.IntegrityError):
            repo.create_rule("orphan", 9999, "return false")

    def test_update(self, mock_db_path):
        repo = CategoryRuleRepository()
        rule = repo.create_rule("r", _category_id(), "return false")

        updated = repo.update_rule(
            rule["id"],
            name="renamed",
            lua_script="return true",
            is_active=False,
            exclude_from_stats=True,
        )

        assert updated is not None
        assert updated["name"] == "renamed"
        assert updated["lua_script"] == "return true"
        assert updated["is_active"] is False
        assert updated["exclude_from_stats"] is True

    def test_update_can_clear_nullable_fields(self, mock_db_path):
        repo = CategoryRuleRepository()
        rule = repo.create_rule(
            "r",
            _category_id(),
            "return false",
            description="d",
            exclude_from_stats=True,
        )

        updated = repo.update_rule(
            rule["id"], description=None, exclude_from_stats=None
        )

        assert updated is not None
        assert updated["description"] is None
        assert updated["exclude_from_stats"] is None

    def test_update_rejects_unknown_fields(self, mock_db_path):
        repo = CategoryRuleRepository()
        rule = repo.create_rule("r", _category_id(), "return false")

        with pytest.raises(ValueError):
            repo.update_rule(rule["id"], id=5)

    def test_update_missing_rule(self, mock_db_path):
        assert CategoryRuleRepository().update_rule(9999, name="x") is None

    def test_update_to_taken_name_is_a_conflict(self, mock_db_path):
        repo = CategoryRuleRepository()
        repo.create_rule("a", _category_id(), "return false")
        b = repo.create_rule("b", _category_id(), "return false")

        with pytest.raises(CategoryRuleExistsError):
            repo.update_rule(b["id"], name="a")

    def test_delete(self, mock_db_path):
        repo = CategoryRuleRepository()
        rule = repo.create_rule("r", _category_id(), "return false")

        assert repo.delete_rule(rule["id"]) is True
        assert repo.delete_rule(rule["id"]) is False
        assert repo.get_rule_by_id(rule["id"]) is None

    def test_deleting_a_category_deletes_its_rules(self, mock_db_path):
        rules = CategoryRuleRepository()
        categories = CategoryRepository()
        custom = categories.create_category("Custom")
        rule = rules.create_rule("r", custom["id"], "return false")

        categories.delete_category(custom["id"])

        assert rules.get_rule_by_id(rule["id"]) is None


@pytest.mark.unit
class TestAssignments:
    @staticmethod
    def _seed() -> tuple[int, int]:
        persist_transactions(
            [
                ("t1", "acc-1", "2025-09-05T10:00:00", -10.0, "EUR", "booked"),
                ("t2", "acc-1", "2025-09-06T10:00:00", -20.0, "EUR", "booked"),
            ]
        )
        rule = CategoryRuleRepository().create_rule(
            "r", _category_id("Groceries"), "return true"
        )
        return rule["id"], _category_id("Groceries")

    def test_apply_records_source_and_rule(self, mock_db_path):
        rule_id, cat = self._seed()

        written = CategoryRuleRepository().apply_assignments(
            [("acc-1", "t1", cat, rule_id, True), ("acc-1", "t2", cat, rule_id, None)]
        )

        assert written == 2
        assert _assignment("acc-1", "t1") == {
            "categoryId": cat,
            "source": "rule",
            "ruleId": rule_id,
            "exclude_from_stats": 1,
        }
        assert _assignment("acc-1", "t2")["exclude_from_stats"] is None

    def test_apply_never_overwrites_a_manual_assignment(self, mock_db_path):
        rule_id, groceries = self._seed()
        dining = _category_id("Dining")
        CategoryRepository().assign_category("acc-1", "t1", dining)

        CategoryRuleRepository().apply_assignments(
            [("acc-1", "t1", groceries, rule_id, None)]
        )

        current = _assignment("acc-1", "t1")
        assert current is not None
        assert current["categoryId"] == dining
        assert current["source"] == "manual"
        assert current["ruleId"] is None

    def test_apply_replaces_a_previous_rule_assignment(self, mock_db_path):
        rule_id, groceries = self._seed()
        other = CategoryRuleRepository().create_rule(
            "o", _category_id("Dining"), "return true"
        )
        repo = CategoryRuleRepository()
        repo.apply_assignments([("acc-1", "t1", groceries, rule_id, None)])

        repo.apply_assignments(
            [("acc-1", "t1", _category_id("Dining"), other["id"], True)]
        )

        current = _assignment("acc-1", "t1")
        assert current is not None
        assert current["categoryId"] == _category_id("Dining")
        assert current["ruleId"] == other["id"]
        assert current["exclude_from_stats"] == 1

    def test_manual_assignment_over_a_rule_one_takes_ownership(self, mock_db_path):
        """The user's choice replaces the rule's, and the row becomes manual
        so the engine leaves it alone from then on."""
        rule_id, groceries = self._seed()
        repo = CategoryRuleRepository()
        repo.apply_assignments([("acc-1", "t1", groceries, rule_id, True)])

        CategoryRepository().assign_category("acc-1", "t1", _category_id("Dining"))

        current = _assignment("acc-1", "t1")
        assert current is not None
        assert current["source"] == "manual"
        assert current["ruleId"] is None
        assert current["exclude_from_stats"] is None

    def test_clear_removes_only_rule_assignments(self, mock_db_path):
        rule_id, groceries = self._seed()
        repo = CategoryRuleRepository()
        repo.apply_assignments([("acc-1", "t1", groceries, rule_id, None)])
        CategoryRepository().assign_category("acc-1", "t2", groceries)

        removed = repo.clear_assignments([("acc-1", "t1"), ("acc-1", "t2")])

        assert removed == 1
        assert _assignment("acc-1", "t1") is None
        assert _assignment("acc-1", "t2") is not None

    def test_deleting_a_rule_removes_its_assignments(self, mock_db_path):
        rule_id, groceries = self._seed()
        repo = CategoryRuleRepository()
        repo.apply_assignments([("acc-1", "t1", groceries, rule_id, None)])

        repo.delete_rule(rule_id)

        assert _assignment("acc-1", "t1") is None

    def test_rule_exclusion_flag_reaches_the_statistics(self, mock_db_path):
        """Rule flag beats the category default, user flag beats the rule."""
        rule_id, groceries = self._seed()  # Groceries is not excluded
        repo = CategoryRuleRepository()
        repo.apply_assignments(
            [
                ("acc-1", "t1", groceries, rule_id, True),
                ("acc-1", "t2", groceries, rule_id, None),
            ]
        )
        transactions = TransactionRepository()

        totals = transactions.get_stats_totals(
            date_from="2025-09-01", date_to="2025-09-30"
        )
        assert totals["total_expenses"] == 20.0  # t1 dropped by the rule

        transactions.set_exclude_from_stats("acc-1", "t1", False)
        totals = transactions.get_stats_totals(
            date_from="2025-09-01", date_to="2025-09-30"
        )
        assert totals["total_expenses"] == 30.0  # user keeps t1 in
