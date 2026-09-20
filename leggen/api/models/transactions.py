"""Query-parameter models for the transaction endpoints.

FastAPI maps a Pydantic model annotated with `Query()` onto individual query
parameters, so the filters are declared once here, documented once in the
OpenAPI schema, and handed to the repository as one `TransactionFilter`.
FastAPI only expands the model when it is the route's sole query argument,
which is why paging and sorting live on the list model rather than beside it.
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from leggen.repositories import TransactionFilter

# A category filter is either a numeric ID or the "uncategorized" bucket.
# Declaring it as a pattern lets FastAPI produce the 422, so the response
# carries field-level errors and the constraint shows up in the schema.
CATEGORY_ID_PATTERN = r"^(\d+|uncategorized)$"

# The two statuses EnableBanking reports for a transaction.
TransactionStatusFilter = Literal["booked", "pending"]

# Money in or money out, by the sign of the amount.
TransactionKind = Literal["income", "expense"]

# Columns the transaction list can be ordered by. Declaring these as Literals
# lets FastAPI reject anything else with a 422 and publish the allowed values
# in the OpenAPI schema, and keeps arbitrary strings away from the ORDER BY.
TransactionSortField = Literal["date", "amount", "description"]
TransactionSortOrder = Literal["asc", "desc"]

_MAGNITUDE_HELP = "transaction size, ignoring sign (matches income and expenses alike)"


class TransactionFilters(BaseModel):
    """The filters shared by the transaction list and its statistics."""

    date_from: date | None = Field(
        default=None, description="Filter from date (YYYY-MM-DD)"
    )
    date_to: date | None = Field(
        default=None, description="Filter to date (YYYY-MM-DD), inclusive"
    )
    account_id: str | None = Field(default=None, description="Filter by account ID")
    category_id: str | None = Field(
        default=None,
        pattern=CATEGORY_ID_PATTERN,
        description="Filter by category ID or 'uncategorized' for transactions without a category",
    )
    status: TransactionStatusFilter | None = Field(
        default=None, description="Filter by transaction status"
    )
    kind: TransactionKind | None = Field(
        default=None, description="Only money in ('income') or money out ('expense')"
    )
    search: str | None = Field(
        default=None, description="Search in transaction descriptions"
    )
    min_amount: float | None = Field(
        default=None, description="Minimum transaction amount"
    )
    max_amount: float | None = Field(
        default=None, description="Maximum transaction amount"
    )
    min_magnitude: float | None = Field(
        default=None, ge=0, description=f"Minimum {_MAGNITUDE_HELP}"
    )
    max_magnitude: float | None = Field(
        default=None, ge=0, description=f"Maximum {_MAGNITUDE_HELP}"
    )

    def to_filter(self) -> TransactionFilter:
        return TransactionFilter(
            account_id=self.account_id,
            date_from=self.date_from.isoformat() if self.date_from else None,
            date_to=self.date_to.isoformat() if self.date_to else None,
            min_amount=self.min_amount,
            max_amount=self.max_amount,
            min_magnitude=self.min_magnitude,
            max_magnitude=self.max_magnitude,
            search=self.search,
            category_id=self.category_id,
            status=self.status,
            kind=self.kind,
        )


class TransactionStatsFilters(TransactionFilters):
    """The same filters, with the date range required."""

    date_from: date = Field(description="Start date (YYYY-MM-DD)")
    date_to: date = Field(description="End date (YYYY-MM-DD), inclusive")


class TransactionListQuery(TransactionFilters):
    """Filters plus the paging and ordering of the transaction list."""

    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    per_page: int = Field(default=50, ge=1, le=500, description="Items per page")
    summary_only: bool = Field(
        default=True, description="Return transaction summaries only"
    )
    sort_by: TransactionSortField = Field(
        default="date", description="Column to order results by"
    )
    sort_order: TransactionSortOrder = Field(
        default="desc", description="Order direction"
    )
