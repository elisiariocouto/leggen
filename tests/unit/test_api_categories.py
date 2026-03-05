"""Tests for categories API endpoints."""

from unittest.mock import MagicMock, patch

import pytest

from leggen.repositories.category_repository import CategoryRepository
from leggen.repositories.transaction_repository import TransactionRepository


@pytest.fixture
def mock_category_repo():
    """Create mock CategoryRepository for testing."""
    return MagicMock()


@pytest.mark.api
class TestCategoriesAPI:
    """Test category-related API endpoints."""

    def test_get_categories_success(
        self,
        fastapi_app,
        api_client,
        mock_config,
        mock_category_repo,
    ):
        """Test successful retrieval of all categories."""
        mock_category_repo.get_all_categories.return_value = [
            {
                "id": 1,
                "name": "Groceries",
                "color": "#22c55e",
                "icon": "shopping-cart",
                "is_default": True,
            },
            {
                "id": 2,
                "name": "Transport",
                "color": "#3b82f6",
                "icon": "car",
                "is_default": True,
            },
        ]

        fastapi_app.dependency_overrides[CategoryRepository] = lambda: (
            mock_category_repo
        )

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get("/api/v1/categories")

        fastapi_app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Groceries"
        assert data[0]["is_default"] is True
        assert data[1]["name"] == "Transport"

    def test_create_category_success(
        self,
        fastapi_app,
        api_client,
        mock_config,
        mock_category_repo,
    ):
        """Test creating a new custom category."""
        mock_category_repo.create_category.return_value = {
            "id": 13,
            "name": "Travel",
            "color": "#06b6d4",
            "icon": None,
            "is_default": False,
        }

        fastapi_app.dependency_overrides[CategoryRepository] = lambda: (
            mock_category_repo
        )

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.post(
                "/api/v1/categories",
                json={"name": "Travel", "color": "#06b6d4"},
            )

        fastapi_app.dependency_overrides.clear()

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Travel"
        assert data["is_default"] is False

    def test_update_category_success(
        self,
        fastapi_app,
        api_client,
        mock_config,
        mock_category_repo,
    ):
        """Test updating a category."""
        mock_category_repo.update_category.return_value = {
            "id": 1,
            "name": "Food & Groceries",
            "color": "#22c55e",
            "icon": "shopping-cart",
            "is_default": True,
        }

        fastapi_app.dependency_overrides[CategoryRepository] = lambda: (
            mock_category_repo
        )

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.put(
                "/api/v1/categories/1",
                json={"name": "Food & Groceries"},
            )

        fastapi_app.dependency_overrides.clear()

        assert response.status_code == 200
        assert response.json()["name"] == "Food & Groceries"

    def test_update_category_not_found(
        self,
        fastapi_app,
        api_client,
        mock_config,
        mock_category_repo,
    ):
        """Test updating a non-existent category."""
        mock_category_repo.update_category.return_value = None

        fastapi_app.dependency_overrides[CategoryRepository] = lambda: (
            mock_category_repo
        )

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.put(
                "/api/v1/categories/999",
                json={"name": "Nonexistent"},
            )

        fastapi_app.dependency_overrides.clear()
        assert response.status_code == 404

    def test_delete_category_success(
        self,
        fastapi_app,
        api_client,
        mock_config,
        mock_category_repo,
    ):
        """Test deleting a custom category."""
        mock_category_repo.delete_category.return_value = True

        fastapi_app.dependency_overrides[CategoryRepository] = lambda: (
            mock_category_repo
        )

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.delete("/api/v1/categories/13")

        fastapi_app.dependency_overrides.clear()
        assert response.status_code == 204

    def test_delete_default_category_rejected(
        self,
        fastapi_app,
        api_client,
        mock_config,
        mock_category_repo,
    ):
        """Test that deleting a default category is rejected."""
        mock_category_repo.delete_category.return_value = False

        fastapi_app.dependency_overrides[CategoryRepository] = lambda: (
            mock_category_repo
        )

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.delete("/api/v1/categories/1")

        fastapi_app.dependency_overrides.clear()
        assert response.status_code == 400

    def test_assign_category_success(
        self,
        fastapi_app,
        api_client,
        mock_config,
        mock_category_repo,
        mock_transaction_repo,
    ):
        """Test assigning a category to a transaction."""
        mock_category_repo.get_category_by_id.return_value = {
            "id": 1,
            "name": "Groceries",
            "color": "#22c55e",
            "icon": "shopping-cart",
            "is_default": True,
        }
        mock_transaction_repo.get_transactions.return_value = [
            {
                "transactionId": "txn-001",
                "description": "LIDL",
                "rawTransaction": {"creditorName": "LIDL GmbH"},
            }
        ]

        fastapi_app.dependency_overrides[CategoryRepository] = lambda: (
            mock_category_repo
        )
        fastapi_app.dependency_overrides[TransactionRepository] = lambda: (
            mock_transaction_repo
        )

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.put(
                "/api/v1/transactions/acc-001/txn-001/category",
                json={"category_id": 1},
            )

        fastapi_app.dependency_overrides.clear()

        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        mock_category_repo.assign_category.assert_called_once()

    def test_assign_category_not_found(
        self,
        fastapi_app,
        api_client,
        mock_config,
        mock_category_repo,
        mock_transaction_repo,
    ):
        """Test assigning a non-existent category."""
        mock_category_repo.get_category_by_id.return_value = None

        fastapi_app.dependency_overrides[CategoryRepository] = lambda: (
            mock_category_repo
        )
        fastapi_app.dependency_overrides[TransactionRepository] = lambda: (
            mock_transaction_repo
        )

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.put(
                "/api/v1/transactions/acc-001/txn-001/category",
                json={"category_id": 999},
            )

        fastapi_app.dependency_overrides.clear()
        assert response.status_code == 404

    def test_remove_category_success(
        self,
        fastapi_app,
        api_client,
        mock_config,
        mock_category_repo,
        mock_transaction_repo,
    ):
        """Test removing a category from a transaction."""
        mock_category_repo.remove_category.return_value = True
        mock_transaction_repo.get_transactions.return_value = [
            {
                "transactionId": "txn-001",
                "description": "LIDL",
                "rawTransaction": {},
            }
        ]

        fastapi_app.dependency_overrides[CategoryRepository] = lambda: (
            mock_category_repo
        )
        fastapi_app.dependency_overrides[TransactionRepository] = lambda: (
            mock_transaction_repo
        )

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.delete(
                "/api/v1/transactions/acc-001/txn-001/category"
            )

        fastapi_app.dependency_overrides.clear()
        assert response.status_code == 200

    def test_suggest_category_success(
        self,
        fastapi_app,
        api_client,
        mock_config,
        mock_category_repo,
        mock_transaction_repo,
    ):
        """Test getting category suggestions for a transaction."""
        mock_transaction_repo.get_transactions.return_value = [
            {
                "transactionId": "txn-001",
                "description": "LIDL GROCERY STORE",
                "rawTransaction": {},
            }
        ]
        mock_category_repo.suggest_category.return_value = [
            {
                "category": {
                    "id": 1,
                    "name": "Groceries",
                    "color": "#22c55e",
                    "icon": "shopping-cart",
                    "is_default": True,
                },
                "score": 15,
                "confidence": "high",
            }
        ]

        fastapi_app.dependency_overrides[CategoryRepository] = lambda: (
            mock_category_repo
        )
        fastapi_app.dependency_overrides[TransactionRepository] = lambda: (
            mock_transaction_repo
        )

        with patch("leggen.utils.config.config", mock_config):
            response = api_client.get(
                "/api/v1/transactions/acc-001/txn-001/suggest-category"
            )

        fastapi_app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["category"]["name"] == "Groceries"
        assert data[0]["confidence"] == "high"
