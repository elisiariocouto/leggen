from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from leggen.services.database_service import DatabaseService


@pytest.fixture
def database_service():
    """Fixture for database service"""
    with patch("leggen.services.database_service.path_manager") as mock_path_manager:
        mock_path_manager.get_database_path.return_value = MagicMock()
        service = DatabaseService()
        return service


@pytest.mark.asyncio
async def test_upsert_transaction_enrichment_create(database_service):
    """Test creating a new transaction enrichment"""
    account_id = "test_account"
    transaction_id = "test_transaction"
    enrichment_data = {
        "clean_name": "Starbucks Coffee",
        "category": "food",
        "logo_url": "https://example.com/starbucks.png",
    }

    # Mock the internal method
    database_service._upsert_transaction_enrichment = MagicMock(
        return_value={
            "accountId": account_id,
            "transactionId": transaction_id,
            "clean_name": "Starbucks Coffee",
            "category": "food",
            "logo_url": "https://example.com/starbucks.png",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
    )

    result = await database_service.upsert_transaction_enrichment(
        account_id, transaction_id, enrichment_data
    )

    assert result["accountId"] == account_id
    assert result["transactionId"] == transaction_id
    assert result["clean_name"] == "Starbucks Coffee"
    assert result["category"] == "food"
    assert result["logo_url"] == "https://example.com/starbucks.png"


@pytest.mark.asyncio
async def test_upsert_transaction_enrichment_update(database_service):
    """Test updating an existing transaction enrichment"""
    account_id = "test_account"
    transaction_id = "test_transaction"
    enrichment_data = {
        "clean_name": "Starbucks",
        "category": "coffee",
    }

    # Mock the internal method
    database_service._upsert_transaction_enrichment = MagicMock(
        return_value={
            "accountId": account_id,
            "transactionId": transaction_id,
            "clean_name": "Starbucks",
            "category": "coffee",
            "logo_url": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
    )

    result = await database_service.upsert_transaction_enrichment(
        account_id, transaction_id, enrichment_data
    )

    assert result["clean_name"] == "Starbucks"
    assert result["category"] == "coffee"


@pytest.mark.asyncio
async def test_get_transaction_enrichment_exists(database_service):
    """Test retrieving an existing transaction enrichment"""
    account_id = "test_account"
    transaction_id = "test_transaction"

    # Mock the internal method
    database_service._get_transaction_enrichment = MagicMock(
        return_value={
            "accountId": account_id,
            "transactionId": transaction_id,
            "clean_name": "Amazon",
            "category": "shopping",
            "logo_url": "https://example.com/amazon.png",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
    )

    result = await database_service.get_transaction_enrichment(
        account_id, transaction_id
    )

    assert result is not None
    assert result["clean_name"] == "Amazon"
    assert result["category"] == "shopping"


@pytest.mark.asyncio
async def test_get_transaction_enrichment_not_found(database_service):
    """Test retrieving a non-existent transaction enrichment"""
    account_id = "test_account"
    transaction_id = "nonexistent_transaction"

    # Mock the internal method to return None
    database_service._get_transaction_enrichment = MagicMock(return_value=None)

    result = await database_service.get_transaction_enrichment(
        account_id, transaction_id
    )

    assert result is None


@pytest.mark.asyncio
async def test_delete_transaction_enrichment_success(database_service):
    """Test deleting an existing transaction enrichment"""
    account_id = "test_account"
    transaction_id = "test_transaction"

    # Mock the internal method
    database_service._delete_transaction_enrichment = MagicMock(return_value=True)

    result = await database_service.delete_transaction_enrichment(
        account_id, transaction_id
    )

    assert result is True


@pytest.mark.asyncio
async def test_delete_transaction_enrichment_not_found(database_service):
    """Test deleting a non-existent transaction enrichment"""
    account_id = "test_account"
    transaction_id = "nonexistent_transaction"

    # Mock the internal method
    database_service._delete_transaction_enrichment = MagicMock(return_value=False)

    result = await database_service.delete_transaction_enrichment(
        account_id, transaction_id
    )

    assert result is False


@pytest.mark.asyncio
async def test_get_transactions_with_enrichments(database_service):
    """Test retrieving transactions includes enrichment data"""
    account_id = "test_account"

    # Mock the internal method with enrichment data
    database_service._get_transactions = MagicMock(
        return_value=[
            {
                "accountId": account_id,
                "transactionId": "txn1",
                "description": "STARBUCKS 12345",
                "transactionValue": -5.50,
                "transactionCurrency": "EUR",
                "transactionDate": "2025-01-01",
                "transactionStatus": "booked",
                "enrichment": {
                    "clean_name": "Starbucks",
                    "category": "food",
                    "logo_url": None,
                },
            },
            {
                "accountId": account_id,
                "transactionId": "txn2",
                "description": "AMAZON EU",
                "transactionValue": -50.00,
                "transactionCurrency": "EUR",
                "transactionDate": "2025-01-02",
                "transactionStatus": "booked",
                # No enrichment for this transaction
            },
        ]
    )

    transactions = await database_service.get_transactions_from_db(
        account_id=account_id
    )

    assert len(transactions) == 2
    # First transaction has enrichment
    assert "enrichment" in transactions[0]
    assert transactions[0]["enrichment"]["clean_name"] == "Starbucks"
    assert transactions[0]["enrichment"]["category"] == "food"
    # Second transaction has no enrichment
    assert "enrichment" not in transactions[1]
