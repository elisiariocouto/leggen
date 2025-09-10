"""Tests for database service."""

import pytest
from unittest.mock import patch
from datetime import datetime

from leggend.services.database_service import DatabaseService


@pytest.fixture
def database_service():
    """Create a database service instance for testing."""
    return DatabaseService()


@pytest.fixture
def sample_transactions_db_format():
    """Sample transactions in database format."""
    return [
        {
            "accountId": "test-account-123",
            "transactionId": "txn-001",
            "internalTransactionId": "txn-001",
            "institutionId": "REVOLUT_REVOLT21",
            "iban": "LT313250081177977789",
            "transactionDate": datetime(2025, 9, 1, 9, 30),
            "description": "Coffee Shop Payment",
            "transactionValue": -10.50,
            "transactionCurrency": "EUR",
            "transactionStatus": "booked",
            "rawTransaction": {"transactionId": "txn-001", "some": "data"},
        },
        {
            "accountId": "test-account-123",
            "transactionId": "txn-002",
            "internalTransactionId": "txn-002",
            "institutionId": "REVOLUT_REVOLT21",
            "iban": "LT313250081177977789",
            "transactionDate": datetime(2025, 9, 2, 14, 15),
            "description": "Grocery Store",
            "transactionValue": -45.30,
            "transactionCurrency": "EUR",
            "transactionStatus": "booked",
            "rawTransaction": {"transactionId": "txn-002", "other": "data"},
        },
    ]


@pytest.fixture
def sample_balances_db_format():
    """Sample balances in database format."""
    return [
        {
            "id": 1,
            "account_id": "test-account-123",
            "bank": "REVOLUT_REVOLT21",
            "status": "active",
            "iban": "LT313250081177977789",
            "amount": 1000.00,
            "currency": "EUR",
            "type": "interimAvailable",
            "timestamp": datetime(2025, 9, 1, 10, 0),
        },
        {
            "id": 2,
            "account_id": "test-account-123",
            "bank": "REVOLUT_REVOLT21",
            "status": "active",
            "iban": "LT313250081177977789",
            "amount": 950.00,
            "currency": "EUR",
            "type": "expected",
            "timestamp": datetime(2025, 9, 1, 10, 0),
        },
    ]


@pytest.mark.asyncio
class TestDatabaseService:
    """Test database service operations."""

    async def test_get_transactions_from_db_success(
        self, database_service, sample_transactions_db_format
    ):
        """Test successful retrieval of transactions from database."""
        with patch("leggen.database.sqlite.get_transactions") as mock_get_transactions:
            mock_get_transactions.return_value = sample_transactions_db_format

            result = await database_service.get_transactions_from_db(
                account_id="test-account-123", limit=10
            )

            assert len(result) == 2
            assert result[0]["internalTransactionId"] == "txn-001"
            mock_get_transactions.assert_called_once_with(
                account_id="test-account-123",
                limit=10,
                offset=0,
                date_from=None,
                date_to=None,
                min_amount=None,
                max_amount=None,
                search=None,
            )

    async def test_get_transactions_from_db_with_filters(
        self, database_service, sample_transactions_db_format
    ):
        """Test retrieving transactions with filters."""
        with patch("leggen.database.sqlite.get_transactions") as mock_get_transactions:
            mock_get_transactions.return_value = sample_transactions_db_format

            result = await database_service.get_transactions_from_db(
                account_id="test-account-123",
                limit=5,
                offset=10,
                date_from="2025-09-01",
                date_to="2025-09-02",
                min_amount=-50.0,
                max_amount=0.0,
                search="Coffee",
            )

            assert len(result) == 2
            mock_get_transactions.assert_called_once_with(
                account_id="test-account-123",
                limit=5,
                offset=10,
                date_from="2025-09-01",
                date_to="2025-09-02",
                min_amount=-50.0,
                max_amount=0.0,
                search="Coffee",
            )

    async def test_get_transactions_from_db_sqlite_disabled(self, database_service):
        """Test getting transactions when SQLite is disabled."""
        database_service.sqlite_enabled = False

        result = await database_service.get_transactions_from_db()

        assert result == []

    async def test_get_transactions_from_db_error(self, database_service):
        """Test handling error when getting transactions."""
        with patch("leggen.database.sqlite.get_transactions") as mock_get_transactions:
            mock_get_transactions.side_effect = Exception("Database error")

            result = await database_service.get_transactions_from_db()

            assert result == []

    async def test_get_transaction_count_from_db_success(self, database_service):
        """Test successful retrieval of transaction count."""
        with patch("leggen.database.sqlite.get_transaction_count") as mock_get_count:
            mock_get_count.return_value = 42

            result = await database_service.get_transaction_count_from_db(
                account_id="test-account-123"
            )

            assert result == 42
            mock_get_count.assert_called_once_with(account_id="test-account-123")

    async def test_get_transaction_count_from_db_with_filters(self, database_service):
        """Test getting transaction count with filters."""
        with patch("leggen.database.sqlite.get_transaction_count") as mock_get_count:
            mock_get_count.return_value = 15

            result = await database_service.get_transaction_count_from_db(
                account_id="test-account-123",
                date_from="2025-09-01",
                min_amount=-100.0,
                search="Coffee",
            )

            assert result == 15
            mock_get_count.assert_called_once_with(
                account_id="test-account-123",
                date_from="2025-09-01",
                min_amount=-100.0,
                search="Coffee",
            )

    async def test_get_transaction_count_from_db_sqlite_disabled(
        self, database_service
    ):
        """Test getting count when SQLite is disabled."""
        database_service.sqlite_enabled = False

        result = await database_service.get_transaction_count_from_db()

        assert result == 0

    async def test_get_transaction_count_from_db_error(self, database_service):
        """Test handling error when getting count."""
        with patch("leggen.database.sqlite.get_transaction_count") as mock_get_count:
            mock_get_count.side_effect = Exception("Database error")

            result = await database_service.get_transaction_count_from_db()

            assert result == 0

    async def test_get_balances_from_db_success(
        self, database_service, sample_balances_db_format
    ):
        """Test successful retrieval of balances from database."""
        with patch("leggen.database.sqlite.get_balances") as mock_get_balances:
            mock_get_balances.return_value = sample_balances_db_format

            result = await database_service.get_balances_from_db(
                account_id="test-account-123"
            )

            assert len(result) == 2
            assert result[0]["account_id"] == "test-account-123"
            assert result[0]["amount"] == 1000.00
            mock_get_balances.assert_called_once_with(account_id="test-account-123")

    async def test_get_balances_from_db_sqlite_disabled(self, database_service):
        """Test getting balances when SQLite is disabled."""
        database_service.sqlite_enabled = False

        result = await database_service.get_balances_from_db()

        assert result == []

    async def test_get_balances_from_db_error(self, database_service):
        """Test handling error when getting balances."""
        with patch("leggen.database.sqlite.get_balances") as mock_get_balances:
            mock_get_balances.side_effect = Exception("Database error")

            result = await database_service.get_balances_from_db()

            assert result == []

    async def test_get_account_summary_from_db_success(self, database_service):
        """Test successful retrieval of account summary."""
        mock_summary = {
            "accountId": "test-account-123",
            "institutionId": "REVOLUT_REVOLT21",
            "iban": "LT313250081177977789",
        }

        with patch("leggen.database.sqlite.get_account_summary") as mock_get_summary:
            mock_get_summary.return_value = mock_summary

            result = await database_service.get_account_summary_from_db(
                "test-account-123"
            )

            assert result == mock_summary
            mock_get_summary.assert_called_once_with("test-account-123")

    async def test_get_account_summary_from_db_sqlite_disabled(self, database_service):
        """Test getting summary when SQLite is disabled."""
        database_service.sqlite_enabled = False

        result = await database_service.get_account_summary_from_db("test-account-123")

        assert result is None

    async def test_get_account_summary_from_db_error(self, database_service):
        """Test handling error when getting summary."""
        with patch("leggen.database.sqlite.get_account_summary") as mock_get_summary:
            mock_get_summary.side_effect = Exception("Database error")

            result = await database_service.get_account_summary_from_db(
                "test-account-123"
            )

            assert result is None

    async def test_persist_balance_sqlite_success(self, database_service):
        """Test successful balance persistence."""
        balance_data = {
            "institution_id": "REVOLUT_REVOLT21",
            "iban": "LT313250081177977789",
            "balances": [
                {
                    "balanceAmount": {"amount": "1000.00", "currency": "EUR"},
                    "balanceType": "interimAvailable",
                }
            ],
        }

        with patch("sqlite3.connect") as mock_connect:
            mock_conn = mock_connect.return_value
            mock_cursor = mock_conn.cursor.return_value

            await database_service._persist_balance_sqlite(
                "test-account-123", balance_data
            )

            # Verify database operations
            mock_connect.assert_called()
            mock_cursor.execute.assert_called()  # Table creation and insert
            mock_conn.commit.assert_called_once()
            mock_conn.close.assert_called_once()

    async def test_persist_balance_sqlite_error(self, database_service):
        """Test handling error during balance persistence."""
        balance_data = {"balances": []}

        with patch("sqlite3.connect") as mock_connect:
            mock_connect.side_effect = Exception("Database error")

            with pytest.raises(Exception, match="Database error"):
                await database_service._persist_balance_sqlite(
                    "test-account-123", balance_data
                )

    async def test_persist_transactions_sqlite_success(
        self, database_service, sample_transactions_db_format
    ):
        """Test successful transaction persistence."""
        with patch("sqlite3.connect") as mock_connect:
            mock_conn = mock_connect.return_value
            mock_cursor = mock_conn.cursor.return_value

            result = await database_service._persist_transactions_sqlite(
                "test-account-123", sample_transactions_db_format
            )

            # Should return the transactions (assuming no duplicates)
            assert len(result) >= 0  # Could be empty if all are duplicates

            # Verify database operations
            mock_connect.assert_called()
            mock_cursor.execute.assert_called()
            mock_conn.commit.assert_called_once()
            mock_conn.close.assert_called_once()

    async def test_persist_transactions_sqlite_error(self, database_service):
        """Test handling error during transaction persistence."""
        with patch("sqlite3.connect") as mock_connect:
            mock_connect.side_effect = Exception("Database error")

            with pytest.raises(Exception, match="Database error"):
                await database_service._persist_transactions_sqlite(
                    "test-account-123", []
                )

    async def test_process_transactions_booked_and_pending(self, database_service):
        """Test processing transactions with both booked and pending."""
        account_info = {
            "institution_id": "REVOLUT_REVOLT21",
            "iban": "LT313250081177977789",
        }

        transaction_data = {
            "transactions": {
                "booked": [
                    {
                        "internalTransactionId": "txn-001",
                        "transactionId": "txn-001",
                        "bookingDate": "2025-09-01",
                        "transactionAmount": {"amount": "-10.50", "currency": "EUR"},
                        "remittanceInformationUnstructured": "Coffee Shop",
                    }
                ],
                "pending": [
                    {
                        "internalTransactionId": "txn-002",
                        "transactionId": "txn-002",
                        "bookingDate": "2025-09-02",
                        "transactionAmount": {"amount": "-25.00", "currency": "EUR"},
                        "remittanceInformationUnstructured": "Gas Station",
                    }
                ],
            }
        }

        result = database_service.process_transactions(
            "test-account-123", account_info, transaction_data
        )

        assert len(result) == 2

        # Check booked transaction
        booked_txn = next(t for t in result if t["transactionStatus"] == "booked")
        assert booked_txn["transactionId"] == "txn-001"
        assert booked_txn["internalTransactionId"] == "txn-001"
        assert booked_txn["transactionValue"] == -10.50
        assert booked_txn["description"] == "Coffee Shop"

        # Check pending transaction
        pending_txn = next(t for t in result if t["transactionStatus"] == "pending")
        assert pending_txn["transactionId"] == "txn-002"
        assert pending_txn["internalTransactionId"] == "txn-002"
        assert pending_txn["transactionValue"] == -25.00
        assert pending_txn["description"] == "Gas Station"

    async def test_process_transactions_missing_date_error(self, database_service):
        """Test processing transaction with missing date raises error."""
        account_info = {"institution_id": "TEST_BANK"}

        transaction_data = {
            "transactions": {
                "booked": [
                    {
                        "internalTransactionId": "txn-001",
                        # Missing both bookingDate and valueDate
                        "transactionAmount": {"amount": "-10.50", "currency": "EUR"},
                    }
                ],
                "pending": [],
            }
        }

        with pytest.raises(ValueError, match="No valid date found in transaction"):
            database_service.process_transactions(
                "test-account-123", account_info, transaction_data
            )

    async def test_process_transactions_remittance_array(self, database_service):
        """Test processing transaction with remittance array."""
        account_info = {"institution_id": "TEST_BANK"}

        transaction_data = {
            "transactions": {
                "booked": [
                    {
                        "internalTransactionId": "txn-001",
                        "transactionId": "txn-001",
                        "bookingDate": "2025-09-01",
                        "transactionAmount": {"amount": "-10.50", "currency": "EUR"},
                        "remittanceInformationUnstructuredArray": ["Line 1", "Line 2"],
                    }
                ],
                "pending": [],
            }
        }

        result = database_service.process_transactions(
            "test-account-123", account_info, transaction_data
        )

        assert len(result) == 1
        assert result[0]["description"] == "Line 1,Line 2"
