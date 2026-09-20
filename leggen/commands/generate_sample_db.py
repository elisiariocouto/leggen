"""Generate sample database command."""

import random
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, TypedDict

import click

from leggen.repositories import (
    AccountRepository,
    BalanceRepository,
    CategoryRepository,
    TransactionRepository,
    run_migrations,
)
from leggen.services.rules import seed_default_category_rules
from leggen.utils.paths import path_manager


class TransactionType(TypedDict):
    """Type definition for transaction type configuration."""

    description: str
    amount_range: tuple[float, float]
    frequency: float


INSTITUTIONS = [
    {"id": "REVOLUT_REVOLT21", "name": "Revolut", "bic": "REVOLT21", "country": "LT"},
    {
        "id": "BANCOBPI_BBPIPTPL",
        "name": "Banco BPI",
        "bic": "BBPIPTPL",
        "country": "PT",
    },
    {"id": "MONZO_MONZGB2L", "name": "Monzo Bank", "bic": "MONZGB2L", "country": "GB"},
    {
        "id": "NUBANK_NUPBBR25",
        "name": "Nu Pagamentos",
        "bic": "NUPBBR25",
        "country": "BR",
    },
]

TRANSACTION_TYPES: list[TransactionType] = [
    {"description": "Grocery Store", "amount_range": (-150, -20), "frequency": 0.3},
    {"description": "Coffee Shop", "amount_range": (-15, -3), "frequency": 0.2},
    {"description": "Gas Station", "amount_range": (-80, -30), "frequency": 0.1},
    {"description": "Online Shopping", "amount_range": (-200, -25), "frequency": 0.15},
    {"description": "Restaurant", "amount_range": (-60, -15), "frequency": 0.15},
    {"description": "Salary", "amount_range": (2500, 5000), "frequency": 0.02},
    {"description": "ATM Withdrawal", "amount_range": (-200, -20), "frequency": 0.05},
    {
        "description": "Transfer to Savings",
        "amount_range": (-1000, -100),
        "frequency": 0.03,
    },
    {
        "description": "Inter-account Transfer",
        "amount_range": (-500, 500),
        "frequency": 0.02,
    },
]

# Merchant names a transaction of each type may carry as its description.
MERCHANTS: dict[str, list[str]] = {
    "Grocery Store": ["TESCO", "SAINSBURY'S", "LIDL", "ALDI", "WALMART", "CARREFOUR"],
    "Coffee Shop": ["STARBUCKS", "COSTA COFFEE", "PRET A MANGER", "LOCAL CAFE"],
    "Gas Station": ["BP", "SHELL", "ESSO", "GALP", "PETROBRAS"],
    "Online Shopping": ["AMAZON", "EBAY", "ZALANDO", "ASOS", "APPLE"],
    "Restaurant": ["PIZZA HUT", "MCDONALD'S", "BURGER KING", "LOCAL RESTAURANT"],
    "Salary": ["MONTHLY SALARY", "PAYROLL DEPOSIT", "SALARY PAYMENT"],
    "ATM Withdrawal": ["ATM WITHDRAWAL", "CASH WITHDRAWAL"],
    "Transfer to Savings": ["SAVINGS TRANSFER", "INVESTMENT TRANSFER"],
    "Inter-account Transfer": [
        "TRANSFER TO CHECKING",
        "TRANSFER FROM SAVINGS",
        "INTERNAL TRANSFER",
    ],
}

# Category each transaction type lands in when categorized by hand.
TYPE_TO_CATEGORY = {
    "Grocery Store": "Groceries",
    "Coffee Shop": "Dining",
    "Gas Station": "Transport",
    "Online Shopping": "Shopping",
    "Restaurant": "Dining",
    "Salary": "Salary",
    "ATM Withdrawal": "Cash",
    "Transfer to Savings": "Transfer",
    "Inter-account Transfer": "Inter-account",
}

# The stored description is the merchant, so resolve categories through it.
MERCHANT_TO_CATEGORY = {
    merchant: TYPE_TO_CATEGORY[type_description]
    for type_description, merchants in MERCHANTS.items()
    for merchant in merchants
}

BALANCE_TYPES = ["interimAvailable", "closingBooked", "authorised"]

# Share of transactions given a category up front; the builtin rules cover
# the rest once the server runs them.
HAND_CATEGORIZED_SHARE = 0.6


class SampleDataGenerator:
    """Generates realistic sample data for testing Leggen."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def prepare_database(self) -> None:
        """Start from an empty, fully migrated database at `db_path`.

        Inserting over an existing file would leave old rows behind: only some
        tables are keyed in a way that lets a re-insert replace them. A leftover
        WAL would also be replayed over the new file on the next connection.
        """
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path.unlink(missing_ok=True)
        for suffix in ("-wal", "-shm"):
            self.db_path.with_name(self.db_path.name + suffix).unlink(missing_ok=True)

        # The repositories resolve their connection through the path manager,
        # so pointing it here is all the plumbing the writes below need.
        path_manager.set_database_path(self.db_path)
        run_migrations()
        seed_default_category_rules()

    def generate_iban(self, country_code: str) -> str:
        """Generate a realistic IBAN for the given country."""
        ibans = {
            "LT": lambda: (
                f"LT{random.randint(10, 99)}{random.randint(10000, 99999)}{random.randint(10000000, 99999999)}"
            ),
            "PT": lambda: (
                f"PT{random.randint(10, 99)}{random.randint(1000, 9999)}{random.randint(1000, 9999)}{random.randint(10000000000, 99999999999)}"
            ),
            "GB": lambda: (
                f"GB{random.randint(10, 99)}MONZ{random.randint(100000, 999999)}{random.randint(100000, 999999)}"
            ),
            "BR": lambda: (
                f"BR{random.randint(10, 99)}{random.randint(10000000, 99999999)}{random.randint(1000, 9999)}{random.randint(10000000, 99999999)}"
            ),
        }
        return ibans.get(
            country_code,
            lambda: (
                f"{country_code}{random.randint(1000000000000000, 9999999999999999)}"
            ),
        )()

    def generate_accounts(self, num_accounts: int = 3) -> list[dict[str, Any]]:
        """Generate sample accounts."""
        accounts = []
        now = datetime.now(UTC)
        base_date = now - timedelta(days=90)

        for i in range(num_accounts):
            institution = random.choice(INSTITUTIONS)
            accounts.append(
                {
                    "id": f"account-{i + 1:03d}-{random.randint(1000, 9999)}",
                    "institution_id": institution["id"],
                    "status": "READY",
                    "iban": self.generate_iban(institution["country"]),
                    "name": f"Personal Account {i + 1}",
                    "currency": "EUR",
                    "created": (
                        base_date + timedelta(days=random.randint(0, 30))
                    ).isoformat(),
                    "last_accessed": (
                        now - timedelta(hours=random.randint(1, 48))
                    ).isoformat(),
                    "last_updated": now.isoformat(),
                }
            )

        return accounts

    def generate_transactions(
        self, accounts: list[dict[str, Any]], num_transactions_per_account: int = 50
    ) -> list[dict[str, Any]]:
        """Generate sample transactions for accounts."""
        transactions = []
        base_date = datetime.now(UTC) - timedelta(days=60)
        weights = [t["frequency"] for t in TRANSACTION_TYPES]

        for account in accounts:
            account_transactions = []

            for i in range(num_transactions_per_account):
                transaction_type = random.choices(TRANSACTION_TYPES, weights=weights)[0]

                min_amount: float
                max_amount: float
                min_amount, max_amount = transaction_type["amount_range"]
                amount = round(random.uniform(min_amount, max_amount), 2)

                # More recent transactions are more likely
                days_ago = random.choices(
                    range(60), weights=[1.5 ** (60 - d) for d in range(60)]
                )[0]
                transaction_date = base_date + timedelta(
                    days=days_ago,
                    hours=random.randint(6, 22),
                    minutes=random.randint(0, 59),
                )

                transaction_id = f"bank-txn-{account['id']}-{i + 1:04d}"
                internal_transaction_id = f"int-txn-{random.randint(100000, 999999)}"

                description = random.choice(
                    MERCHANTS.get(
                        transaction_type["description"],
                        [transaction_type["description"]],
                    )
                )

                # Most are booked; some recent ones might be pending
                status = (
                    "pending" if days_ago < 2 and random.random() < 0.1 else "booked"
                )

                # Raw transaction mirroring EnableBanking's snake_case payload
                # (the sync stores the provider dict unmodified)
                raw_transaction: dict[str, Any] = {
                    "transaction_id": transaction_id,
                    "entry_reference": internal_transaction_id,
                    "booking_date": transaction_date.strftime("%Y-%m-%d"),
                    "value_date": transaction_date.strftime("%Y-%m-%d"),
                    "transaction_amount": {
                        "amount": str(abs(amount)),
                        "currency": account["currency"],
                    },
                    "credit_debit_indicator": "DBIT" if amount < 0 else "CRDT",
                    "remittance_information": [description],
                    "status": "BOOK" if status == "booked" else "PDNG",
                    "bank_transaction_code": {
                        "code": "PMNT" if amount < 0 else "RCDT",
                    },
                }

                # Counterparty details are bank-dependent — include them most
                # of the time so both shapes show up in the data
                counterparty = {"name": description.title()}
                counterparty_iban = (
                    f"DE{random.randint(10, 99)}{random.randint(10**17, 10**18 - 1)}"
                )
                if amount < 0:
                    raw_transaction["creditor"] = counterparty
                    if random.random() < 0.7:
                        raw_transaction["creditor_account"] = {
                            "iban": counterparty_iban
                        }
                else:
                    raw_transaction["debtor"] = counterparty
                    if random.random() < 0.7:
                        raw_transaction["debtor_account"] = {"iban": counterparty_iban}

                account_transactions.append(
                    {
                        "accountId": account["id"],
                        "transactionId": transaction_id,
                        "internalTransactionId": internal_transaction_id,
                        "institutionId": account["institution_id"],
                        "iban": account["iban"],
                        # Naive, like the dates the sync derives from the bank's
                        # booking dates
                        "transactionDate": transaction_date.replace(
                            tzinfo=None
                        ).isoformat(),
                        "description": description,
                        "transactionValue": amount,
                        "transactionCurrency": account["currency"],
                        "transactionStatus": status,
                        "rawTransaction": raw_transaction,
                    }
                )

            # Sort transactions by date for realistic ordering
            account_transactions.sort(key=lambda x: x["transactionDate"])
            transactions.extend(account_transactions)

        return transactions

    def generate_balances(self, accounts: list[dict[str, Any]]) -> list[tuple]:
        """Generate one balance row per type for every account, in the row
        shape BalanceRepository.persist stores."""
        balances = []
        timestamp = datetime.now(UTC).isoformat()

        for account in accounts:
            base_balance = random.uniform(500, 2000)

            for balance_type in BALANCE_TYPES:
                # Add some variation between balance types
                variation = (
                    random.uniform(-50, 50) if balance_type != "interimAvailable" else 0
                )
                balances.append(
                    (
                        account["id"],
                        account["institution_id"],
                        account["status"],
                        account["iban"],
                        round(base_balance + variation, 2),
                        account["currency"],
                        balance_type,
                        timestamp,
                    )
                )

        return balances

    def insert_data(
        self,
        accounts: list[dict[str, Any]],
        transactions: list[dict[str, Any]],
        balances: list[tuple],
    ) -> None:
        """Write the generated data through the same repositories the sync
        uses, so the sample database has exactly the columns the server reads."""
        account_repo = AccountRepository()
        for account in accounts:
            account_repo.persist(account)

        transaction_repo = TransactionRepository()
        for account in accounts:
            transaction_repo.persist(
                account["id"],
                [t for t in transactions if t["accountId"] == account["id"]],
            )

        balance_repo = BalanceRepository()
        for account in accounts:
            balance_repo.persist(
                account["id"], [b for b in balances if b[0] == account["id"]]
            )

        self._assign_categories(transactions)

    def _assign_categories(self, transactions: list[dict[str, Any]]) -> None:
        """Give a share of the transactions a manual category, by description."""
        category_repo = CategoryRepository()
        # The defaults are seeded by the baseline migration
        category_ids = {c["name"]: c["id"] for c in category_repo.get_all_categories()}

        for transaction in transactions:
            if random.random() > HAND_CATEGORIZED_SHARE:
                continue
            category = MERCHANT_TO_CATEGORY.get(transaction["description"])
            if category is None or category not in category_ids:
                continue
            category_repo.assign_category(
                transaction["accountId"],
                transaction["transactionId"],
                category_ids[category],
            )

    def generate_sample_database(
        self, num_accounts: int = 3, num_transactions_per_account: int = 50
    ):
        """Generate complete sample database."""
        click.echo(f"🗄️  Creating sample database at: {self.db_path}")
        self.prepare_database()

        click.echo(f"👥 Generating {num_accounts} sample accounts...")
        accounts = self.generate_accounts(num_accounts)

        click.echo(
            f"💳 Generating {num_transactions_per_account} transactions per account..."
        )
        transactions = self.generate_transactions(
            accounts, num_transactions_per_account
        )

        click.echo("💰 Generating account balances...")
        balances = self.generate_balances(accounts)

        click.echo("💾 Inserting data into database...")
        self.insert_data(accounts, transactions, balances)

        click.echo("\n✅ Sample database created successfully!")
        click.echo("📊 Summary:")
        click.echo(f"   - Accounts: {len(accounts)}")
        click.echo(f"   - Transactions: {len(transactions)}")
        click.echo(f"   - Balances: {len(balances)}")
        click.echo(f"   - Database: {self.db_path}")

        click.echo("\n📋 Sample accounts:")
        for account in accounts:
            institution_name = next(
                inst["name"]
                for inst in INSTITUTIONS
                if inst["id"] == account["institution_id"]
            )
            click.echo(f"   - {account['id']} ({institution_name}) - {account['iban']}")


@click.command()
@click.option(
    "--database",
    type=click.Path(path_type=Path),
    help=(
        "Path to database file (default: the global --database flag or "
        "LEGGEN_DATABASE_PATH, else ~/.config/leggen/leggen-dev.db)"
    ),
)
@click.option(
    "--accounts",
    type=int,
    default=3,
    help="Number of sample accounts to generate (default: 3)",
)
@click.option(
    "--transactions",
    type=int,
    default=50,
    help="Number of transactions per account (default: 50)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing database without confirmation",
)
@click.pass_context
def generate_sample_db(
    ctx: click.Context,
    database: Path | None,
    accounts: int,
    transactions: int,
    force: bool,
):
    """Generate a sample database with realistic financial data for testing."""
    # Never default to the production database: without an explicit path
    # the sample data goes to a development file next to it.
    db_path = (
        database
        or path_manager.configured_database_path()
        or path_manager.get_config_dir() / "leggen-dev.db"
    )

    if db_path.exists() and not force:
        click.echo(f"⚠️  Database already exists: {db_path}")
        if not click.confirm("Do you want to overwrite it?"):
            click.echo("Aborted.")
            ctx.exit(0)

    SampleDataGenerator(db_path).generate_sample_database(accounts, transactions)

    click.echo("\n🚀 Usage instructions:")
    click.echo("To use this sample database with leggen commands:")
    click.echo(f"   export LEGGEN_DATABASE_PATH={db_path}")
    click.echo("   leggen transactions")
    click.echo("")
    click.echo("To use this sample database with leggen server:")
    click.echo(f"   leggen --database {db_path} server")
