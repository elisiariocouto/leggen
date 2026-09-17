"""Tests for the category rule endpoints."""

import pytest

from leggen.repositories import CategoryRepository
from tests.conftest import persist_transactions


def _category(name: str) -> int:
    return next(
        c for c in CategoryRepository().get_all_categories() if c["name"] == name
    )["id"]


def _create(api_client, **overrides) -> dict:
    body = {
        "name": "Supermarkets",
        "category_id": _category("Groceries"),
        "lua_script": 'return contains(tx.description, "Transaction t1")',
        "priority": 10,
    }
    body.update(overrides)
    response = api_client.post("/api/v1/category-rules", json=body)
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.api
class TestRuleCrud:
    def test_create_returns_the_rule(self, api_client, mock_db_path):
        rule = _create(api_client, description="Big chains")

        assert rule["name"] == "Supermarkets"
        assert rule["category_name"] == "Groceries"
        assert rule["priority"] == 10
        assert rule["is_active"] is True
        assert rule["is_default"] is False
        assert rule["exclude_from_stats"] is None
        assert rule["description"] == "Big chains"

    def test_list_in_evaluation_order(self, api_client, mock_db_path):
        _create(api_client, name="later", priority=200)
        _create(api_client, name="first", priority=1)

        response = api_client.get("/api/v1/category-rules")

        assert [r["name"] for r in response.json()] == ["first", "later"]

    def test_get_one(self, api_client, mock_db_path):
        rule = _create(api_client)

        response = api_client.get(f"/api/v1/category-rules/{rule['id']}")

        assert response.status_code == 200
        assert response.json()["id"] == rule["id"]

    def test_get_missing_is_404(self, api_client, mock_db_path):
        response = api_client.get("/api/v1/category-rules/999")

        assert response.status_code == 404
        assert response.json()["code"] == "NOT_FOUND"

    def test_create_with_unknown_category_is_404(self, api_client, mock_db_path):
        response = api_client.post(
            "/api/v1/category-rules",
            json={"name": "x", "category_id": 9999, "lua_script": "return true"},
        )

        assert response.status_code == 404

    def test_create_with_bad_script_is_422(self, api_client, mock_db_path):
        response = api_client.post(
            "/api/v1/category-rules",
            json={
                "name": "x",
                "category_id": _category("Groceries"),
                "lua_script": "if then",
            },
        )

        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "INVALID_RULE_SCRIPT"
        assert "line 1" in body["detail"]

    def test_duplicate_name_is_409(self, api_client, mock_db_path):
        _create(api_client)

        response = api_client.post(
            "/api/v1/category-rules",
            json={
                "name": "Supermarkets",
                "category_id": _category("Groceries"),
                "lua_script": "return true",
            },
        )

        assert response.status_code == 409
        assert response.json()["code"] == "CATEGORY_RULE_EXISTS"

    def test_update_changes_only_the_fields_sent(self, api_client, mock_db_path):
        rule = _create(api_client, description="keep me")

        response = api_client.put(
            f"/api/v1/category-rules/{rule['id']}",
            json={"priority": 5, "is_active": False, "exclude_from_stats": True},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["priority"] == 5
        assert body["is_active"] is False
        assert body["exclude_from_stats"] is True
        assert body["description"] == "keep me"
        assert body["lua_script"] == rule["lua_script"]

    def test_update_can_clear_nullable_fields(self, api_client, mock_db_path):
        rule = _create(api_client, description="d", exclude_from_stats=True)

        response = api_client.put(
            f"/api/v1/category-rules/{rule['id']}",
            json={"description": None, "exclude_from_stats": None},
        )

        assert response.json()["description"] is None
        assert response.json()["exclude_from_stats"] is None

    def test_update_validates_the_script(self, api_client, mock_db_path):
        rule = _create(api_client)

        response = api_client.put(
            f"/api/v1/category-rules/{rule['id']}", json={"lua_script": "return ("}
        )

        assert response.status_code == 422
        assert response.json()["code"] == "INVALID_RULE_SCRIPT"

    def test_update_validates_the_category(self, api_client, mock_db_path):
        rule = _create(api_client)

        response = api_client.put(
            f"/api/v1/category-rules/{rule['id']}", json={"category_id": 9999}
        )

        assert response.status_code == 404

    def test_update_missing_is_404(self, api_client, mock_db_path):
        response = api_client.put("/api/v1/category-rules/999", json={"priority": 1})

        assert response.status_code == 404

    def test_delete(self, api_client, mock_db_path):
        rule = _create(api_client)

        assert (
            api_client.delete(f"/api/v1/category-rules/{rule['id']}").status_code == 204
        )
        assert (
            api_client.delete(f"/api/v1/category-rules/{rule['id']}").status_code == 404
        )

    def test_requires_auth(self, fastapi_app, mock_db_path):
        from fastapi.testclient import TestClient

        response = TestClient(fastapi_app).get("/api/v1/category-rules")

        assert response.status_code == 401


@pytest.mark.api
class TestReference:
    def test_lists_functions_fields_and_examples(self, api_client, mock_db_path):
        response = api_client.get("/api/v1/category-rules/reference")

        assert response.status_code == 200
        body = response.json()
        signatures = [f["signature"] for g in body["stdlib"] for f in g["functions"]]
        assert any(s.startswith("contains(") for s in signatures)
        names = [f["name"] for g in body["fields"] for f in g["fields"]]
        assert "tx.merchant" in names and "tx.raw" in names
        assert body["max_instructions"] > 0
        assert body["examples"] and all("lua_script" in e for e in body["examples"])

    def test_examples_compile(self, api_client, mock_db_path):
        """Every example in the reference must be a valid script."""
        from leggen.services.rules import validate_script

        for example in api_client.get("/api/v1/category-rules/reference").json()[
            "examples"
        ]:
            assert validate_script(example["lua_script"]) is None, example["title"]


@pytest.mark.api
class TestAuthoringHelpers:
    @pytest.fixture(autouse=True)
    def transactions(self, mock_db_path):
        persist_transactions(
            [
                ("t1", "acc-1", "2025-09-05T10:00:00", -30.0, "EUR", "booked"),
                ("t2", "acc-1", "2025-09-06T10:00:00", -15.0, "EUR", "booked"),
                ("t3", "acc-1", "2025-09-07T10:00:00", 2000.0, "EUR", "booked"),
            ]
        )

    def test_test_endpoint_returns_result_and_logs(self, api_client):
        response = api_client.post(
            "/api/v1/category-rules/test",
            json={
                "lua_script": "log(tx.amount) return tx.is_expense",
                "account_id": "acc-1",
                "transaction_id": "t1",
            },
        )

        assert response.status_code == 200
        assert response.json() == {"matched": True, "error": None, "logs": ["-30.0"]}

    def test_test_endpoint_reports_runtime_errors(self, api_client):
        response = api_client.post(
            "/api/v1/category-rules/test",
            json={
                "lua_script": "return tx.raw.a.b",
                "account_id": "acc-1",
                "transaction_id": "t1",
            },
        )

        assert response.status_code == 200
        assert response.json()["matched"] is False
        assert "attempt to index" in response.json()["error"]

    def test_test_endpoint_rejects_syntax_errors(self, api_client):
        response = api_client.post(
            "/api/v1/category-rules/test",
            json={
                "lua_script": "if then",
                "account_id": "acc-1",
                "transaction_id": "t1",
            },
        )

        assert response.status_code == 422
        assert response.json()["code"] == "INVALID_RULE_SCRIPT"

    def test_test_endpoint_unknown_transaction(self, api_client):
        response = api_client.post(
            "/api/v1/category-rules/test",
            json={
                "lua_script": "return true",
                "account_id": "acc-1",
                "transaction_id": "nope",
            },
        )

        assert response.status_code == 404

    def test_preview_paginates_and_flags_manual(self, api_client):
        CategoryRepository().assign_category("acc-1", "t1", _category("Dining"))

        response = api_client.post(
            "/api/v1/category-rules/preview",
            json={"lua_script": "return tx.is_expense", "per_page": 1, "page": 1},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 2
        assert body["evaluated"] == 3
        assert body["total_pages"] == 2
        assert body["has_next"] is True
        assert len(body["data"]) == 1
        first = body["data"][0]
        assert first["transaction_id"] == "t1"
        assert first["manual"] is True
        assert first["category_name"] == "Dining"

    def test_preview_with_no_matches(self, api_client):
        response = api_client.post(
            "/api/v1/category-rules/preview", json={"lua_script": "return false"}
        )

        body = response.json()
        assert body["total"] == 0
        assert body["total_pages"] == 1
        assert body["data"] == []

    def test_apply_dry_run_then_for_real(self, api_client):
        _create(api_client, lua_script="return tx.is_expense")

        dry = api_client.post("/api/v1/category-rules/apply?dry_run=true").json()
        assert dry["dry_run"] is True
        assert dry["assigned"] == 2
        assert {c["transaction_id"] for c in dry["changes"]} == {"t1", "t2"}
        assert all(c["action"] == "assign" for c in dry["changes"])
        listed = api_client.get("/api/v1/transactions").json()["data"]
        assert all(t["category_id"] is None for t in listed)

        real = api_client.post("/api/v1/category-rules/apply").json()
        assert real["dry_run"] is False
        assert real["assigned"] == 2
        listed = api_client.get("/api/v1/transactions").json()["data"]
        assert sum(t["category_name"] == "Groceries" for t in listed) == 2

    def test_apply_reports_skipped_and_erroring_rules(self, api_client):
        # A rule that does not compile cannot be created through the API,
        # so plant it directly.
        from leggen.repositories import CategoryRuleRepository

        repo = CategoryRuleRepository()
        broken = repo.create_rule("broken", _category("Shopping"), "if then")
        faulty = repo.create_rule(
            "faulty", _category("Shopping"), "return tx.raw.a.b == 1"
        )

        report = api_client.post("/api/v1/category-rules/apply").json()

        assert report["skipped_rules"] == [
            {"rule_id": broken["id"], "error": report["skipped_rules"][0]["error"]}
        ]
        assert "line 1" in report["skipped_rules"][0]["error"]
        assert report["errors"][0]["rule_id"] == faulty["id"]
        assert report["errors"][0]["count"] == 3
