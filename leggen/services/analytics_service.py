"""Analytics aggregations for the dashboard.

The SQL lives in the repositories; this module holds the logic SQLite cannot
express — merchant identity from a raw payload, cadence detection, and carrying
balances forward across gaps in sync history.
"""

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any

from leggen.repositories.balance_repository import BalanceRepository
from leggen.repositories.transaction_repository import TransactionRepository
from leggen.services.data_processors import merchant_identity

# A recurring charge is rarely billed on an exact 30-day grid: month lengths
# differ, and weekends push debits by a day or two.
_CADENCES: list[tuple[str, float, float]] = [
    ("weekly", 7, 2),
    ("biweekly", 14, 3),
    ("monthly", 30.44, 5),
    ("quarterly", 91.3, 10),
    ("yearly", 365.25, 20),
]

# Below this many charges a repeating pattern is indistinguishable from
# coincidence.
_MIN_OCCURRENCES = 3

# Real subscription prices drift (FX, VAT, plan changes) without becoming a
# different commitment.
_AMOUNT_TOLERANCE = 0.15


def _parse_day(value: str) -> date | None:
    """Parse a stored transaction/balance date, which may carry a time part."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
        except ValueError:
            return None


def get_net_worth(
    balance_repo: BalanceRepository,
    date_from: str,
    date_to: str,
    account_id: str | None = None,
) -> dict[str, Any]:
    """Total balance across accounts over time, from recorded snapshots.

    A sync that misses one account leaves that account without a snapshot for
    the day. Net worth is a stock rather than a flow, so the last known balance
    is carried forward instead of counting the account as zero — otherwise the
    total dips by a whole account balance whenever a single sync fails.
    """
    rows = balance_repo.get_net_worth_series(date_from, date_to, account_id)
    if not rows:
        return {
            "points": [],
            "currency": None,
            "change": 0.0,
            "change_pct": None,
        }

    currency = rows[0].get("currency")

    by_day: dict[str, dict[str, float]] = defaultdict(dict)
    labels: dict[str, str] = {}
    for row in rows:
        key = row["series_key"]
        by_day[row["day"]][key] = row["amount"]
        labels[key] = row["account_id"]

    points: list[dict[str, Any]] = []
    carried: dict[str, float] = {}
    for day in sorted(by_day):
        carried.update(by_day[day])
        accounts = {labels.get(key, key): amount for key, amount in carried.items()}
        points.append(
            {
                "date": day,
                "total": round(sum(carried.values()), 2),
                "accounts": {name: round(v, 2) for name, v in accounts.items()},
            }
        )

    first: float = points[0]["total"]
    last: float = points[-1]["total"]
    change = round(last - first, 2)
    # A percentage against a zero or negative opening balance is not meaningful.
    change_pct = round((change / first) * 100, 2) if first > 0 else None

    return {
        "points": points,
        "currency": currency,
        "change": change,
        "change_pct": change_pct,
    }


def get_merchants(
    transaction_repo: TransactionRepository,
    date_from: str,
    date_to: str,
    account_id: str | None = None,
    limit: int = 15,
) -> dict[str, Any]:
    """Top merchants by spend, compared against the preceding window.

    The comparison window is the same length as the requested one and ends the
    day before it starts, so "last 30 days" compares against the 30 before it.
    """
    rows, currency = transaction_repo.get_expense_rows(
        date_from, date_to, account_id=account_id
    )
    if not rows:
        return {"merchants": [], "currency": None, "uncategorized_share": 0.0}

    start = _parse_day(date_from)
    end = _parse_day(date_to)
    previous: dict[str, float] = {}
    if start and end:
        span = (end - start).days + 1
        prev_end = start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=span - 1)
        prev_rows, _ = transaction_repo.get_expense_rows(
            prev_start.isoformat(),
            prev_end.isoformat(),
            account_id=account_id,
            currency=currency,
        )
        for row in prev_rows:
            if row["transactionValue"] >= 0:
                continue
            key, _ = merchant_identity(row["rawTransaction"], row["description"], True)
            previous[key] = previous.get(key, 0.0) + abs(row["transactionValue"])

    totals: dict[str, float] = defaultdict(float)
    counts: dict[str, int] = defaultdict(int)
    display: dict[str, str] = {}
    uncategorized = 0
    expenses = 0

    for row in rows:
        if row["transactionValue"] >= 0:
            continue
        expenses += 1
        if row.get("categoryId") is None:
            uncategorized += 1
        key, name = merchant_identity(row["rawTransaction"], row["description"], True)
        totals[key] += abs(row["transactionValue"])
        counts[key] += 1
        display.setdefault(key, name)

    merchants = []
    for key, total in sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[
        :limit
    ]:
        prev = previous.get(key, 0.0)
        merchants.append(
            {
                "merchant": display[key],
                "total": round(total, 2),
                "transaction_count": counts[key],
                "previous_total": round(prev, 2),
                # No prior spend means "new", which is not a 0% change.
                "change_pct": round(((total - prev) / prev) * 100, 2) if prev else None,
            }
        )

    return {
        "merchants": merchants,
        "currency": currency,
        "uncategorized_share": round(uncategorized / expenses, 4) if expenses else 0.0,
    }


def _classify_cadence(gaps: list[float]) -> str | None:
    """Name the cadence a series of day-gaps fits, if any."""
    if not gaps:
        return None
    average = sum(gaps) / len(gaps)
    for name, period, tolerance in _CADENCES:
        if abs(average - period) > tolerance:
            continue
        # The average alone would accept an irregular series that happens to
        # average out, so require each gap to sit near the period too.
        if all(abs(gap - period) <= tolerance * 1.5 for gap in gaps):
            return name
    return None


def _recurring_weight(detected: dict[str, Any]) -> float:
    """Total spent on one detected commitment, used for ranking."""
    return float(detected["typical_amount"]) * float(detected["occurrences"])


def get_recurring(
    transaction_repo: TransactionRepository,
    date_from: str,
    date_to: str,
    account_id: str | None = None,
) -> list[dict[str, Any]]:
    """Detect charges that repeat on a regular cadence.

    Heuristic by nature: merchants are grouped by normalized description, and
    a merchant billing several different subscriptions appears once per amount
    cluster. Results carry the amount, cadence and last-seen date so a wrong
    grouping is visible rather than silently folded into a total.
    """
    rows, currency = transaction_repo.get_expense_rows(
        date_from, date_to, account_id=account_id
    )
    if not rows:
        return []

    charges: dict[str, list[tuple[date, float]]] = defaultdict(list)
    display: dict[str, str] = {}
    for row in rows:
        if row["transactionValue"] >= 0:
            continue
        day = _parse_day(row["transactionDate"])
        if day is None:
            continue
        key, name = merchant_identity(row["rawTransaction"], row["description"], True)
        charges[key].append((day, abs(row["transactionValue"])))
        display.setdefault(key, name)

    detected: list[dict[str, Any]] = []
    for key, entries in charges.items():
        if len(entries) < _MIN_OCCURRENCES:
            continue
        entries.sort()

        # One merchant can bill several plans; cluster by amount so a €5 and a
        # €50 charge are not averaged into a fictional €27 subscription.
        clusters: list[list[tuple[date, float]]] = []
        for day, amount in entries:
            for cluster in clusters:
                reference = cluster[0][1]
                if abs(amount - reference) <= reference * _AMOUNT_TOLERANCE:
                    cluster.append((day, amount))
                    break
            else:
                clusters.append([(day, amount)])

        for cluster in clusters:
            if len(cluster) < _MIN_OCCURRENCES:
                continue
            days = [day for day, _ in cluster]
            # Two charges on one day are one purchase, not a cadence.
            unique_days = sorted(set(days))
            if len(unique_days) < _MIN_OCCURRENCES:
                continue
            gaps = [
                (b - a).days for a, b in zip(unique_days, unique_days[1:], strict=False)
            ]
            cadence = _classify_cadence([float(g) for g in gaps])
            if cadence is None:
                continue

            amounts = [amount for _, amount in cluster]
            typical = sorted(amounts)[len(amounts) // 2]
            last_seen = unique_days[-1]
            period = next(p for name, p, _ in _CADENCES if name == cadence)
            detected.append(
                {
                    "merchant": display[key],
                    "cadence": cadence,
                    "typical_amount": round(typical, 2),
                    "occurrences": len(cluster),
                    "last_seen": last_seen.isoformat(),
                    "next_expected": (
                        last_seen + timedelta(days=round(period))
                    ).isoformat(),
                    "currency": currency,
                }
            )

    # Rank by total spent on the commitment, so a small monthly charge can
    # outrank a large one-off-looking yearly bill.
    detected.sort(key=_recurring_weight, reverse=True)
    return detected
