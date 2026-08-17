"""Tests for the analytics dashboard endpoints."""

import pytest

from tests.conftest import persist_transactions


def _persist_rich(rows: list[dict]) -> None:
    """Seed transactions with per-row description and raw payload.

    The shared `persist_transactions` helper fixes both, but merchant grouping
    and recurrence detection are driven entirely by those two fields.
    """
    from leggen.repositories import TransactionRepository

    repo = TransactionRepository()
    by_account: dict[str, list] = {}
    for row in rows:
        txn = {
            "transactionId": row["id"],
            "internalTransactionId": f"int-{row['id']}",
            "institutionId": "TEST_BANK",
            "iban": "LT313250081177977789",
            "accountId": row.get("account_id", "acc-1"),
            "transactionDate": row["date"],
            "description": row.get("description", "Payment"),
            "transactionValue": row["value"],
            "transactionCurrency": row.get("currency", "EUR"),
            "transactionStatus": "booked",
            "rawTransaction": row.get("raw", {}),
        }
        by_account.setdefault(txn["accountId"], []).append(txn)
    for account_id, txns in by_account.items():
        repo.persist(account_id, txns)


def _persist_balances(rows: list[tuple]) -> None:
    """Insert balance snapshots: (account_id, iban, amount, type, timestamp)."""
    from leggen.repositories import BalanceRepository

    repo = BalanceRepository()
    for account_id, iban, amount, btype, timestamp in rows:
        repo.persist(
            account_id,
            [
                (
                    account_id,
                    "TEST_BANK",
                    "enabled",
                    iban,
                    amount,
                    "EUR",
                    btype,
                    timestamp,
                )
            ],
        )


@pytest.mark.api
class TestCashFlow:
    """Monthly income/expense with a running cumulative net."""

    def test_cash_flow_success(self, api_client, mock_db_path):
        persist_transactions(
            [
                ("t1", "acc-1", "2025-09-05T10:00:00", 1000.00, "EUR", "booked"),
                ("t2", "acc-1", "2025-09-20T10:00:00", -400.00, "EUR", "booked"),
                ("t3", "acc-1", "2025-10-05T10:00:00", 1000.00, "EUR", "booked"),
                ("t4", "acc-1", "2025-10-20T10:00:00", -250.00, "EUR", "booked"),
            ]
        )

        response = api_client.get(
            "/api/v1/analytics/cash-flow?date_from=2025-09-01&date_to=2025-10-31"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["currency"] == "EUR"
        assert data["total_income"] == 2000.00
        assert data["total_expenses"] == 650.00
        assert data["net"] == 1350.00
        assert data["average_monthly_net"] == 675.00  # 1350 over 2 months

        assert [p["month"] for p in data["points"]] == ["2025-09", "2025-10"]
        assert data["points"][0]["net"] == 600.00  # 1000 - 400
        assert data["points"][1]["net"] == 750.00  # 1000 - 250
        # Cumulative carries the running total forward
        assert data["points"][0]["cumulative_net"] == 600.00
        assert data["points"][1]["cumulative_net"] == 1350.00

    def test_cash_flow_excludes_flagged_categories(self, api_client, mock_db_path):
        """Categories flagged exclude_from_stats stay out of the totals."""
        from leggen.repositories import CategoryRepository

        persist_transactions(
            [
                ("t1", "acc-1", "2025-09-05T10:00:00", -100.00, "EUR", "booked"),
                ("t2", "acc-1", "2025-09-06T10:00:00", -50.00, "EUR", "booked"),
            ]
        )
        # "Inter-account" is seeded with exclude_from_stats set.
        repo = CategoryRepository()
        excluded = next(c for c in repo.get_all_categories() if c["exclude_from_stats"])
        repo.assign_category("acc-1", "t1", excluded["id"])

        response = api_client.get(
            "/api/v1/analytics/cash-flow?date_from=2025-09-01&date_to=2025-09-30"
        )

        assert response.status_code == 200
        assert response.json()["total_expenses"] == 50.00  # t1 excluded

    def test_cash_flow_uses_dominant_currency(self, api_client, mock_db_path):
        persist_transactions(
            [
                ("t1", "acc-1", "2025-09-05T10:00:00", -10.00, "EUR", "booked"),
                ("t2", "acc-1", "2025-09-06T10:00:00", -20.00, "EUR", "booked"),
                ("t3", "acc-1", "2025-09-07T10:00:00", -999.00, "USD", "booked"),
            ]
        )

        response = api_client.get(
            "/api/v1/analytics/cash-flow?date_from=2025-09-01&date_to=2025-09-30"
        )

        data = response.json()
        assert data["currency"] == "EUR"
        assert data["total_expenses"] == 30.00  # USD not mixed in

    def test_cash_flow_empty(self, api_client, mock_db_path):
        response = api_client.get(
            "/api/v1/analytics/cash-flow?date_from=2025-09-01&date_to=2025-09-30"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["points"] == []
        assert data["net"] == 0


@pytest.mark.api
class TestNetWorth:
    """Net worth from recorded balance snapshots."""

    def test_sums_accounts_per_day(self, api_client, mock_db_path):
        _persist_balances(
            [
                ("acc-1", "PT50001", 100.00, "closingBooked", "2025-09-01T10:00:00"),
                ("acc-2", "PT50002", 250.00, "closingBooked", "2025-09-01T10:00:00"),
                ("acc-1", "PT50001", 120.00, "closingBooked", "2025-09-02T10:00:00"),
                ("acc-2", "PT50002", 250.00, "closingBooked", "2025-09-02T10:00:00"),
            ]
        )

        response = api_client.get(
            "/api/v1/analytics/net-worth?date_from=2025-09-01&date_to=2025-09-02"
        )

        assert response.status_code == 200
        data = response.json()
        assert [p["total"] for p in data["points"]] == [350.00, 370.00]
        assert data["change"] == 20.00

    def test_survives_account_id_change(self, api_client, mock_db_path):
        """One real account keeps one series when its account_id changes.

        This codebase has seen provider UUIDs replaced by IBANs; grouping on
        the IBAN is what stops that showing up as a cliff in net worth.
        """
        _persist_balances(
            [
                ("old-uuid", "PT50001", 500.00, "closingBooked", "2025-09-01T10:00:00"),
                ("PT50001", "PT50001", 500.00, "closingBooked", "2025-09-02T10:00:00"),
            ]
        )

        response = api_client.get(
            "/api/v1/analytics/net-worth?date_from=2025-09-01&date_to=2025-09-02"
        )

        data = response.json()
        # Same money throughout: no doubling on the changeover day, no drop.
        assert [p["total"] for p in data["points"]] == [500.00, 500.00]
        assert data["change"] == 0.0

    def test_carries_balance_forward_over_a_missed_sync(self, api_client, mock_db_path):
        """An account missing from one day's sync keeps its last balance.

        Net worth is a stock, so a missed sync must not read as the account
        having emptied.
        """
        _persist_balances(
            [
                ("acc-1", "PT50001", 100.00, "closingBooked", "2025-09-01T10:00:00"),
                ("acc-2", "PT50002", 200.00, "closingBooked", "2025-09-01T10:00:00"),
                # Only acc-1 syncs on the 2nd
                ("acc-1", "PT50001", 110.00, "closingBooked", "2025-09-02T10:00:00"),
            ]
        )

        response = api_client.get(
            "/api/v1/analytics/net-worth?date_from=2025-09-01&date_to=2025-09-02"
        )

        data = response.json()
        assert [p["total"] for p in data["points"]] == [300.00, 310.00]

    def test_prefers_closing_booked_over_interim(self, api_client, mock_db_path):
        """Only one balance type per account per day, or it double-counts."""
        _persist_balances(
            [
                ("acc-1", "PT50001", 100.00, "closingBooked", "2025-09-01T10:00:00"),
                ("acc-1", "PT50001", 95.00, "interimAvailable", "2025-09-01T10:05:00"),
            ]
        )

        response = api_client.get(
            "/api/v1/analytics/net-worth?date_from=2025-09-01&date_to=2025-09-01"
        )

        data = response.json()
        assert [p["total"] for p in data["points"]] == [100.00]

    def test_empty(self, api_client, mock_db_path):
        response = api_client.get(
            "/api/v1/analytics/net-worth?date_from=2025-09-01&date_to=2025-09-30"
        )
        assert response.status_code == 200
        assert response.json()["points"] == []


@pytest.mark.api
class TestMerchants:
    """Merchant grouping and period-over-period comparison."""

    def test_groups_noisy_descriptions(self, api_client, mock_db_path):
        """Reference numbers must not split one merchant into several."""
        _persist_rich(
            [
                {
                    "id": "t1",
                    "date": "2025-09-05T10:00:00",
                    "value": -20.00,
                    "description": "COMPRA 3007 Uber * Eats",
                },
                {
                    "id": "t2",
                    "date": "2025-09-06T10:00:00",
                    "value": -30.00,
                    "description": "COMPRA 4102 Uber   *eats Pending",
                },
            ]
        )

        response = api_client.get(
            "/api/v1/analytics/merchants?date_from=2025-09-01&date_to=2025-09-30"
        )

        assert response.status_code == 200
        merchants = response.json()["merchants"]
        assert len(merchants) == 1
        assert merchants[0]["total"] == 50.00
        assert merchants[0]["transaction_count"] == 2

    def test_uses_creditor_name_when_present(self, api_client, mock_db_path):
        _persist_rich(
            [
                {
                    "id": "t1",
                    "date": "2025-09-05T10:00:00",
                    "value": -20.00,
                    "description": "PAG BXVAL- 3007 NOISE",
                    "raw": {"creditor": {"name": "Continente Bom Dia"}},
                }
            ]
        )

        response = api_client.get(
            "/api/v1/analytics/merchants?date_from=2025-09-01&date_to=2025-09-30"
        )

        assert response.json()["merchants"][0]["merchant"] == "Continente Bom Dia"

    def test_compares_against_preceding_window(self, api_client, mock_db_path):
        """The comparison window has equal length and ends the day before."""
        _persist_rich(
            [
                # Previous window: 2025-08-02..2025-08-31
                {
                    "id": "p1",
                    "date": "2025-08-10T10:00:00",
                    "value": -100.00,
                    "description": "Tesco",
                },
                # Current window: 2025-09-01..2025-09-30
                {
                    "id": "t1",
                    "date": "2025-09-10T10:00:00",
                    "value": -150.00,
                    "description": "Tesco",
                },
            ]
        )

        response = api_client.get(
            "/api/v1/analytics/merchants?date_from=2025-09-01&date_to=2025-09-30"
        )

        merchant = response.json()["merchants"][0]
        assert merchant["total"] == 150.00
        assert merchant["previous_total"] == 100.00
        assert merchant["change_pct"] == 50.00

    def test_new_merchant_has_no_change_pct(self, api_client, mock_db_path):
        """No prior spend is "new", which is not a 0% change."""
        _persist_rich(
            [
                {
                    "id": "t1",
                    "date": "2025-09-10T10:00:00",
                    "value": -75.00,
                    "description": "Brand New Shop",
                }
            ]
        )

        response = api_client.get(
            "/api/v1/analytics/merchants?date_from=2025-09-01&date_to=2025-09-30"
        )

        merchant = response.json()["merchants"][0]
        assert merchant["previous_total"] == 0.0
        assert merchant["change_pct"] is None

    def test_income_is_excluded(self, api_client, mock_db_path):
        _persist_rich(
            [
                {
                    "id": "t1",
                    "date": "2025-09-10T10:00:00",
                    "value": 2000.00,
                    "description": "SALARY",
                },
                {
                    "id": "t2",
                    "date": "2025-09-11T10:00:00",
                    "value": -25.00,
                    "description": "Tesco",
                },
            ]
        )

        response = api_client.get(
            "/api/v1/analytics/merchants?date_from=2025-09-01&date_to=2025-09-30"
        )

        merchants = response.json()["merchants"]
        assert len(merchants) == 1
        assert merchants[0]["merchant"] == "Tesco"

    def test_reports_uncategorized_share(self, api_client, mock_db_path):
        """The widget needs to say how much of the spend is uncategorized."""
        _persist_rich(
            [
                {
                    "id": "t1",
                    "date": "2025-09-10T10:00:00",
                    "value": -10.00,
                    "description": "A Shop",
                },
                {
                    "id": "t2",
                    "date": "2025-09-11T10:00:00",
                    "value": -10.00,
                    "description": "B Shop",
                },
            ]
        )

        response = api_client.get(
            "/api/v1/analytics/merchants?date_from=2025-09-01&date_to=2025-09-30"
        )

        assert response.json()["uncategorized_share"] == 1.0


@pytest.mark.api
class TestRecurring:
    """Cadence detection over merchant/amount clusters."""

    def test_detects_a_monthly_subscription(self, api_client, mock_db_path):
        _persist_rich(
            [
                {
                    "id": f"t{i}",
                    "date": date,
                    "value": -9.99,
                    "description": "Apple.com/bill",
                }
                for i, date in enumerate(
                    [
                        "2025-07-01T10:00:00",
                        "2025-08-01T10:00:00",
                        "2025-09-01T10:00:00",
                        "2025-10-01T10:00:00",
                    ]
                )
            ]
        )

        response = api_client.get(
            "/api/v1/analytics/recurring?date_from=2025-07-01&date_to=2025-10-31"
        )

        assert response.status_code == 200
        detected = response.json()
        assert len(detected) == 1
        assert detected[0]["cadence"] == "monthly"
        assert detected[0]["typical_amount"] == 9.99
        assert detected[0]["occurrences"] == 4
        assert detected[0]["last_seen"] == "2025-10-01"
        assert detected[0]["next_expected"] == "2025-10-31"

    def test_ignores_irregular_charges(self, api_client, mock_db_path):
        """Random dates at one merchant are not a commitment."""
        _persist_rich(
            [
                {
                    "id": f"t{i}",
                    "date": date,
                    "value": -20.00,
                    "description": "Random Shop",
                }
                for i, date in enumerate(
                    [
                        "2025-07-01T10:00:00",
                        "2025-07-03T10:00:00",
                        "2025-08-19T10:00:00",
                        "2025-10-27T10:00:00",
                    ]
                )
            ]
        )

        response = api_client.get(
            "/api/v1/analytics/recurring?date_from=2025-07-01&date_to=2025-10-31"
        )

        assert response.json() == []

    def test_requires_a_minimum_number_of_occurrences(self, api_client, mock_db_path):
        """Two charges a month apart are not yet a pattern."""
        _persist_rich(
            [
                {
                    "id": "t1",
                    "date": "2025-08-01T10:00:00",
                    "value": -9.99,
                    "description": "Netflix",
                },
                {
                    "id": "t2",
                    "date": "2025-09-01T10:00:00",
                    "value": -9.99,
                    "description": "Netflix",
                },
            ]
        )

        response = api_client.get(
            "/api/v1/analytics/recurring?date_from=2025-07-01&date_to=2025-10-31"
        )

        assert response.json() == []

    def test_separates_amount_clusters_at_one_merchant(self, api_client, mock_db_path):
        """A merchant billing two plans is two commitments, not one average."""
        rows = []
        for i, date in enumerate(
            ["2025-07-02T10:00:00", "2025-08-02T10:00:00", "2025-09-02T10:00:00"]
        ):
            rows.append(
                {
                    "id": f"a{i}",
                    "date": date,
                    "value": -5.00,
                    "description": "Apple.com/bill",
                }
            )
            rows.append(
                {
                    "id": f"b{i}",
                    "date": date,
                    "value": -50.00,
                    "description": "Apple.com/bill",
                }
            )
        _persist_rich(rows)

        response = api_client.get(
            "/api/v1/analytics/recurring?date_from=2025-07-01&date_to=2025-09-30"
        )

        detected = response.json()
        assert sorted(d["typical_amount"] for d in detected) == [5.00, 50.00]

    def test_tolerates_small_price_drift(self, api_client, mock_db_path):
        """A subscription that changes price slightly is still one commitment."""
        _persist_rich(
            [
                {
                    "id": f"t{i}",
                    "date": date,
                    "value": value,
                    "description": "Gym Membership",
                }
                for i, (date, value) in enumerate(
                    [
                        ("2025-07-05T10:00:00", -28.90),
                        ("2025-08-05T10:00:00", -29.90),
                        ("2025-09-05T10:00:00", -30.90),
                    ]
                )
            ]
        )

        response = api_client.get(
            "/api/v1/analytics/recurring?date_from=2025-07-01&date_to=2025-09-30"
        )

        detected = response.json()
        assert len(detected) == 1
        assert detected[0]["occurrences"] == 3
