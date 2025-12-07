"""Analytics processor for calculating historical balances and statistics."""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger


class AnalyticsProcessor:
    """Calculates historical balances and transaction statistics from database data."""

    def calculate_historical_balances(
        self,
        db_path: Path,
        account_id: Optional[str] = None,
        days: int = 365,
    ) -> List[Dict[str, Any]]:
        """
        Generate historical balance progression based on transaction history.

        Uses current balances and subtracts future transactions to calculate
        balance at each historical point in time.

        Args:
            db_path: Path to SQLite database
            account_id: Optional account ID to filter by
            days: Number of days to look back (default 365)

        Returns:
            List of historical balance data points
        """
        if not db_path.exists():
            return []

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).date().isoformat()
            today_date = datetime.now().date().isoformat()

            # Single SQL query to generate historical balances using window functions
            query = """
            WITH RECURSIVE date_series AS (
                -- Generate weekly dates from cutoff_date to today
                SELECT date(?) as ref_date
                UNION ALL
                SELECT date(ref_date, '+7 days')
                FROM date_series
                WHERE ref_date < date(?)
            ),
            current_balances AS (
                -- Get current balance for each account/type
                SELECT account_id, type, amount, currency
                FROM balances b1
                WHERE b1.timestamp = (
                    SELECT MAX(b2.timestamp)
                    FROM balances b2
                    WHERE b2.account_id = b1.account_id AND b2.type = b1.type
                )
                {account_filter}
                AND b1.type = 'closingBooked'  -- Focus on closingBooked for charts
            ),
            historical_points AS (
                -- Calculate balance at each weekly point by subtracting future transactions
                SELECT
                    cb.account_id,
                    cb.type as balance_type,
                    cb.currency,
                    ds.ref_date,
                    cb.amount - COALESCE(
                        (SELECT SUM(t.transactionValue)
                         FROM transactions t
                         WHERE t.accountId = cb.account_id
                         AND date(t.transactionDate) > ds.ref_date), 0
                    ) as balance_amount
                FROM current_balances cb
                CROSS JOIN date_series ds
            )
            SELECT
                account_id || '_' || balance_type || '_' || ref_date as id,
                account_id,
                balance_amount,
                balance_type,
                currency,
                ref_date as reference_date
            FROM historical_points
            ORDER BY account_id, ref_date
            """

            # Build parameters and account filter
            params = [cutoff_date, today_date]
            if account_id:
                account_filter = "AND b1.account_id = ?"
                params.append(account_id)
            else:
                account_filter = ""

            # Format the query with conditional filter
            formatted_query = query.format(account_filter=account_filter)

            cursor.execute(formatted_query, params)
            rows = cursor.fetchall()

            conn.close()
            return [dict(row) for row in rows]

        except Exception as e:
            conn.close()
            logger.error(f"Failed to calculate historical balances: {e}")
            raise

    def calculate_monthly_stats(
        self,
        db_path: Path,
        account_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Calculate monthly transaction statistics aggregated from database.

        Sums transactions by month and calculates income, expenses, and net values.

        Args:
            db_path: Path to SQLite database
            account_id: Optional account ID to filter by
            date_from: Optional start date (ISO format)
            date_to: Optional end date (ISO format)

        Returns:
            List of monthly statistics with income, expenses, and net totals
        """
        if not db_path.exists():
            return []

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # SQL query to aggregate transactions by month
            query = """
            SELECT
                strftime('%Y-%m', transactionDate) as month,
                COALESCE(SUM(CASE WHEN transactionValue > 0 THEN transactionValue ELSE 0 END), 0) as income,
                COALESCE(SUM(CASE WHEN transactionValue < 0 THEN ABS(transactionValue) ELSE 0 END), 0) as expenses,
                COALESCE(SUM(transactionValue), 0) as net
            FROM transactions
            WHERE 1=1
            """

            params = []

            if account_id:
                query += " AND accountId = ?"
                params.append(account_id)

            if date_from:
                query += " AND transactionDate >= ?"
                params.append(date_from)

            if date_to:
                query += " AND transactionDate <= ?"
                params.append(date_to)

            query += """
            GROUP BY strftime('%Y-%m', transactionDate)
            ORDER BY month ASC
            """

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Convert to desired format with proper month display
            monthly_stats = []
            for row in rows:
                # Convert YYYY-MM to display format like "Mar 2024"
                year, month_num = row["month"].split("-")
                month_date = datetime.strptime(f"{year}-{month_num}-01", "%Y-%m-%d")
                display_month = month_date.strftime("%b %Y")

                monthly_stats.append(
                    {
                        "month": display_month,
                        "income": round(row["income"], 2),
                        "expenses": round(row["expenses"], 2),
                        "net": round(row["net"], 2),
                    }
                )

            conn.close()
            return monthly_stats

        except Exception as e:
            conn.close()
            logger.error(f"Failed to calculate monthly stats: {e}")
            raise
