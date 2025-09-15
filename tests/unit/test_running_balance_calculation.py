"""Tests for running balance calculation logic in frontend.

This test validates the running balance calculation algorithm to ensure
it correctly computes account balances after each transaction.
"""

import pytest


class TestRunningBalanceCalculation:
    """Test running balance calculation logic."""

    def test_running_balance_calculation_logic(self):
        """Test the logic behind running balance calculation.
        
        This test validates the algorithm used in the frontend TransactionsTable
        component to ensure running balances are calculated correctly.
        """
        # Sample test data similar to what the frontend receives
        transactions = [
            {
                "transaction_id": "txn-1",
                "account_id": "account-001",
                "transaction_value": -100.00,
                "transaction_date": "2025-01-01T10:00:00Z",
                "description": "Initial expense"
            },
            {
                "transaction_id": "txn-2", 
                "account_id": "account-001",
                "transaction_value": 500.00,
                "transaction_date": "2025-01-02T10:00:00Z", 
                "description": "Salary"
            },
            {
                "transaction_id": "txn-3",
                "account_id": "account-001", 
                "transaction_value": -50.00,
                "transaction_date": "2025-01-03T10:00:00Z",
                "description": "Shopping"
            }
        ]

        balances = [
            {
                "account_id": "account-001",
                "balance_amount": 350.00,  # Final balance after all transactions
                "balance_type": "interimAvailable"
            }
        ]

        # Implement the corrected algorithm from the frontend
        running_balances = self._calculate_running_balances(transactions, balances)

        # Expected running balances:
        # - After txn-1 (-100): balance should be -100.00
        # - After txn-2 (+500): balance should be 400.00 (previous + 500)
        # - After txn-3 (-50): balance should be 350.00 (previous - 50)
        
        assert running_balances["account-001-txn-1"] == -100.00, "First transaction running balance incorrect"
        assert running_balances["account-001-txn-2"] == 400.00, "Second transaction running balance incorrect"
        assert running_balances["account-001-txn-3"] == 350.00, "Third transaction running balance incorrect"
        
        # Final balance should match current account balance
        final_calculated_balance = running_balances["account-001-txn-3"]
        assert final_calculated_balance == balances[0]["balance_amount"], "Final balance doesn't match current account balance"

    def test_running_balance_multiple_accounts(self):
        """Test running balance calculation with multiple accounts."""
        transactions = [
            {
                "transaction_id": "txn-1",
                "account_id": "account-001",
                "transaction_value": -50.00,
                "transaction_date": "2025-01-01T10:00:00Z",
                "description": "Account 1 expense"
            },
            {
                "transaction_id": "txn-2",
                "account_id": "account-002",
                "transaction_value": -25.00,
                "transaction_date": "2025-01-01T11:00:00Z",
                "description": "Account 2 expense"
            },
            {
                "transaction_id": "txn-3",
                "account_id": "account-001",
                "transaction_value": 100.00,
                "transaction_date": "2025-01-02T10:00:00Z",
                "description": "Account 1 income"
            }
        ]

        balances = [
            {
                "account_id": "account-001",
                "balance_amount": 50.00,
                "balance_type": "interimAvailable"
            },
            {
                "account_id": "account-002",
                "balance_amount": 75.00,
                "balance_type": "interimAvailable"
            }
        ]

        running_balances = self._calculate_running_balances(transactions, balances)

        # Account 1: starts at 0, -50 = -50, +100 = 50
        assert running_balances["account-001-txn-1"] == -50.00
        assert running_balances["account-001-txn-3"] == 50.00
        
        # Account 2: starts at 100, -25 = 75
        assert running_balances["account-002-txn-2"] == 75.00

    def test_running_balance_empty_transactions(self):
        """Test running balance calculation with no transactions."""
        transactions = []
        balances = [
            {
                "account_id": "account-001",
                "balance_amount": 100.00,
                "balance_type": "interimAvailable"
            }
        ]

        running_balances = self._calculate_running_balances(transactions, balances)
        assert running_balances == {}

    def test_running_balance_no_balances(self):
        """Test running balance calculation with no balance data."""
        transactions = [
            {
                "transaction_id": "txn-1",
                "account_id": "account-001",
                "transaction_value": -50.00,
                "transaction_date": "2025-01-01T10:00:00Z",
                "description": "Expense"
            }
        ]
        balances = []

        running_balances = self._calculate_running_balances(transactions, balances)
        
        # When no balance data available, current balance is 0
        # Working backwards: starting_balance = 0 - (-50) = 50
        # Going forward: running_balance = 50 + (-50) = 0
        assert running_balances["account-001-txn-1"] == 0.00

    def _calculate_running_balances(self, transactions, balances):
        """
        Implementation of the corrected running balance calculation algorithm.
        This mirrors the logic implemented in the frontend TransactionsTable component.
        """
        running_balances = {}
        account_balance_map = {}

        # Create a map of account current balances - use interimAvailable as the most current
        for balance in balances:
            if balance["balance_type"] == "interimAvailable":
                account_balance_map[balance["account_id"]] = balance["balance_amount"]

        # Group transactions by account
        transactions_by_account = {}
        for txn in transactions:
            account_id = txn["account_id"]
            if account_id not in transactions_by_account:
                transactions_by_account[account_id] = []
            transactions_by_account[account_id].append(txn)

        # Calculate running balance for each account
        for account_id, account_transactions in transactions_by_account.items():
            current_balance = account_balance_map.get(account_id, 0)

            # Sort transactions by date (oldest first) for forward calculation
            sorted_transactions = sorted(
                account_transactions,
                key=lambda x: x["transaction_date"]
            )

            # Calculate the starting balance by working backwards from current balance
            starting_balance = current_balance
            for txn in reversed(sorted_transactions):
                starting_balance -= txn["transaction_value"]

            # Now calculate running balances going forward chronologically
            running_balance = starting_balance
            for txn in sorted_transactions:
                running_balance += txn["transaction_value"]
                running_balances[f"{txn['account_id']}-{txn['transaction_id']}"] = running_balance

        return running_balances