"""Tests for the categories API endpoints, against the real temporary database.

The default categories are seeded by the migrations, so every test starts
with them present.
"""

import pytest

from leggen.errors import CategoryExistsError
from leggen.repositories.category_repository import CategoryRepository
from tests.helpers import (
    category_assignments,
    category_id,
    persist_transactions,
    seed_transactions,
)


def _create(api_client, name: str = "Travel", **fields) -> dict:
    response = api_client.post(
        "/api/v1/categories", json={"name": name, "color": "#06b6d4", **fields}
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.api
class TestCategoriesAPI:
    def test_get_categories_lists_the_defaults(self, api_client):
        response = api_client.get("/api/v1/categories")

        assert response.status_code == 200
        data = response.json()
        names = [c["name"] for c in data]
        assert "Groceries" in names
        assert all(c["is_default"] is True for c in data)

    def test_create_category(self, api_client):
        created = _create(api_client, "Travel")

        assert created["name"] == "Travel"
        assert created["color"] == "#06b6d4"
        assert created["is_default"] is False
        assert created["exclude_from_stats"] is False

        listed = api_client.get("/api/v1/categories").json()
        assert {"id": created["id"], "name": "Travel"} in [
            {"id": c["id"], "name": c["name"]} for c in listed
        ]
        # Custom categories sort after the defaults.
        assert listed[-1]["name"] == "Travel"

    def test_create_category_with_exclude_from_stats(self, api_client):
        created = _create(api_client, "Internal", exclude_from_stats=True)

        assert created["exclude_from_stats"] is True
        assert CategoryRepository().get_category_by_id(created["id"])[
            "exclude_from_stats"
        ]

    def test_update_category(self, api_client):
        created = _create(api_client, "Travel")

        response = api_client.put(
            f"/api/v1/categories/{created['id']}",
            json={"name": "Trips", "color": "#000000"},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Trips"
        assert response.json()["color"] == "#000000"
        stored = CategoryRepository().get_category_by_id(created["id"])
        assert stored["name"] == "Trips"

    def test_update_category_not_found(self, api_client):
        response = api_client.put(
            "/api/v1/categories/999", json={"name": "Nonexistent"}
        )

        assert response.status_code == 404

    def test_delete_custom_category(self, api_client):
        created = _create(api_client, "Travel")

        response = api_client.delete(f"/api/v1/categories/{created['id']}")

        assert response.status_code == 204
        assert CategoryRepository().get_category_by_id(created["id"]) is None

    def test_delete_default_category_rejected(self, api_client):
        groceries = category_id("Groceries")

        response = api_client.delete(f"/api/v1/categories/{groceries}")

        assert response.status_code == 400
        assert CategoryRepository().get_category_by_id(groceries) is not None

    def test_delete_unknown_category_rejected(self, api_client):
        response = api_client.delete("/api/v1/categories/999")

        assert response.status_code == 400


@pytest.mark.api
class TestTransactionCategoryAssignment:
    def test_assign_category(self, api_client):
        persist_transactions(
            [("txn-001", "acc-001", "2025-09-01T10:00:00", -12.0, "EUR", "booked")]
        )
        groceries = category_id("Groceries")

        response = api_client.put(
            "/api/v1/transactions/acc-001/txn-001/category",
            json={"category_id": groceries},
        )

        assert response.status_code == 204
        assignment = category_assignments()["txn-001"]
        assert assignment["categoryId"] == groceries
        assert assignment["source"] == "manual"

    def test_assign_unknown_category(self, api_client):
        response = api_client.put(
            "/api/v1/transactions/acc-001/txn-001/category",
            json={"category_id": 999},
        )

        assert response.status_code == 404
        assert category_assignments() == {}

    def test_remove_category(self, api_client):
        persist_transactions(
            [("txn-001", "acc-001", "2025-09-01T10:00:00", -12.0, "EUR", "booked")]
        )
        CategoryRepository().assign_category(
            "acc-001", "txn-001", category_id("Groceries")
        )

        response = api_client.delete("/api/v1/transactions/acc-001/txn-001/category")

        assert response.status_code == 204
        assert category_assignments() == {}

    def test_remove_category_when_none_assigned(self, api_client):
        response = api_client.delete("/api/v1/transactions/acc-001/txn-001/category")

        assert response.status_code == 404


@pytest.mark.api
class TestBulkCategorization:
    DESCRIPTION = "To Flexible Cash Funds"

    def _seed(self) -> None:
        seed_transactions(
            [
                {"id": "t1", "description": self.DESCRIPTION, "value": -100.0},
                {"id": "t2", "description": self.DESCRIPTION, "value": -200.0},
                {"id": "t3", "description": "Something else", "value": -5.0},
            ]
        )

    def test_bulk_categorize_by_description(self, api_client):
        self._seed()
        transport = category_id("Transport")

        response = api_client.put(
            "/api/v1/transactions/bulk-categorize",
            json={"category_id": transport, "description": self.DESCRIPTION},
        )

        assert response.status_code == 200
        assert response.json() == {"updated_count": 2}
        assignments = category_assignments()
        assert set(assignments) == {"t1", "t2"}
        assert all(a["categoryId"] == transport for a in assignments.values())

    def test_bulk_categorize_unknown_category(self, api_client):
        self._seed()

        response = api_client.put(
            "/api/v1/transactions/bulk-categorize",
            json={"category_id": 999, "description": self.DESCRIPTION},
        )

        assert response.status_code == 404

    def test_bulk_categorize_without_matches(self, api_client):
        self._seed()

        response = api_client.put(
            "/api/v1/transactions/bulk-categorize",
            json={
                "category_id": category_id("Transport"),
                "description": "Nonexistent description",
            },
        )

        assert response.status_code == 200
        assert response.json()["updated_count"] == 0

    def test_bulk_remove_by_description(self, api_client):
        self._seed()
        transport = category_id("Transport")
        api_client.put(
            "/api/v1/transactions/bulk-categorize",
            json={"category_id": transport, "description": self.DESCRIPTION},
        )
        CategoryRepository().assign_category("acc-1", "t3", transport)

        response = api_client.request(
            "DELETE",
            "/api/v1/transactions/bulk-categorize",
            json={"description": self.DESCRIPTION},
        )

        assert response.status_code == 200
        assert response.json() == {"removed_count": 2}
        # Only the matching descriptions lose their category.
        assert set(category_assignments()) == {"t3"}

    def test_bulk_remove_without_matches(self, api_client):
        response = api_client.request(
            "DELETE",
            "/api/v1/transactions/bulk-categorize",
            json={"description": "Nonexistent"},
        )

        assert response.status_code == 200
        assert response.json()["removed_count"] == 0


@pytest.mark.api
class TestDuplicateCategory:
    """A duplicate category name is a conflict, not a server error."""

    def test_create_duplicate_returns_409(self, api_client):
        _create(api_client, "Travel")

        response = api_client.post(
            "/api/v1/categories", json={"name": "Travel", "color": "#06b6d4"}
        )

        assert response.status_code == 409
        body = response.json()
        assert body["code"] == "CATEGORY_EXISTS"
        assert body["detail"] == "Category 'Travel' already exists."

    def test_repository_translates_unique_violation(self, mock_db_path):
        """The real INSERT must raise the domain error, not sqlite3.IntegrityError."""
        repo = CategoryRepository()
        repo.create_category(name="Travel", color="#06b6d4")

        with pytest.raises(CategoryExistsError):
            repo.create_category(name="Travel", color="#06b6d4")
