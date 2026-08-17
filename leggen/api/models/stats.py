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
    currency: str | None = None
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
    currency: str | None = None


class CategoryStats(BaseModel):
    """Income/expense totals for one category"""

    category_id: int | None = None
    category_name: str
    category_color: str
    transaction_count: int
    income: float
    expenses: float
    currency: str | None = None


class CashFlowPoint(BaseModel):
    """One month of cash flow, with the running total to that point."""

    month: str
    income: float
    expenses: float
    net: float
    cumulative_net: float
    transaction_count: int


class CashFlow(BaseModel):
    """Cash flow over the period, answering "am I saving or burning?"."""

    points: list[CashFlowPoint]
    currency: str | None = None
    total_income: float
    total_expenses: float
    net: float
    # Mean monthly net across whole months in the range; the caller shows this
    # as the "typical month" line.
    average_monthly_net: float


class NetWorthPoint(BaseModel):
    """Total balance across accounts at one point in time."""

    date: str
    total: float
    # Per-account balances keyed by display name, for the stacked breakdown.
    accounts: dict[str, float]


class NetWorth(BaseModel):
    """Net worth over time, built from recorded balance snapshots.

    Snapshots are written at sync time, so resolution equals sync frequency
    and the series starts at the first sync rather than at account opening.
    """

    points: list[NetWorthPoint]
    currency: str | None = None
    change: float
    change_pct: float | None = None


class MerchantStats(BaseModel):
    """Spending with one merchant, compared to the preceding window."""

    merchant: str
    total: float
    transaction_count: int
    previous_total: float
    # None when the merchant is absent from the previous window, which is
    # different from a 0% change.
    change_pct: float | None = None


class Merchants(BaseModel):
    """Top merchants for the period, plus the largest movers."""

    merchants: list[MerchantStats]
    currency: str | None = None
    uncategorized_share: float


class RecurringPayment(BaseModel):
    """A charge that repeats on a regular cadence.

    Detection is heuristic: merchants are grouped by normalized description,
    so an unusual description may be missed or mis-grouped.
    """

    merchant: str
    cadence: str
    typical_amount: float
    occurrences: int
    last_seen: str
    next_expected: str | None = None
    currency: str | None = None
