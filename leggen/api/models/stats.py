from typing import Optional

from pydantic import BaseModel


class TransactionStats(BaseModel):
    """Aggregate totals for a filtered set of transactions.

    Money totals cover only the dominant currency of the set (summing across
    currencies is meaningless); counts cover every matching transaction.
    """

    date_from: str
    date_to: str
    total_transactions: int
    booked_transactions: int
    pending_transactions: int
    currency: Optional[str] = None
    total_income: float
    total_expenses: float
    net_change: float
    average_transaction: float
    accounts_included: int


class MonthlyStats(BaseModel):
    """Income/expense totals for one month"""

    month: str
    income: float
    expenses: float
    net: float
    currency: Optional[str] = None


class CategoryStats(BaseModel):
    """Income/expense totals for one category"""

    category_id: Optional[int] = None
    category_name: str
    category_color: str
    transaction_count: int
    income: float
    expenses: float
    currency: Optional[str] = None
