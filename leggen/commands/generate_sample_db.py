"""Generate sample database command."""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, TypedDict

import click

from leggen.repositories import ensure_tables
from leggen.repositories.db import create_connection
from leggen.utils.keywords import extract_keywords
from leggen.utils.paths import path_manager


class TransactionType(TypedDict):
    """Type definition for transaction type configuration."""

    description: str
    amount_range: tuple[float, float]
    frequency: float


DESCRIPTION_TO_CATEGORY = {
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


class SampleDataGenerator:
    """Generates realistic sample data for testing Leggen."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.institutions = [
            {
                "id": "REVOLUT_REVOLT21",
                "name": "Revolut",
                "bic": "REVOLT21",
                "country": "LT",
            },
            {
                "id": "BANCOBPI_BBPIPTPL",
                "name": "Banco BPI",
                "bic": "BBPIPTPL",
                "country": "PT",
            },
            {
                "id": "MONZO_MONZGB2L",
                "name": "Monzo Bank",
                "bic": "MONZGB2L",
                "country": "GB",
            },
            {
                "id": "NUBANK_NUPBBR25",
                "name": "Nu Pagamentos",
                "bic": "NUPBBR25",
                "country": "BR",
            },
        ]

        self.transaction_types: list[TransactionType] = [
            {
                "description": "Grocery Store",
                "amount_range": (-150, -20),
                "frequency": 0.3,
            },
            {"description": "Coffee Shop", "amount_range": (-15, -3), "frequency": 0.2},
            {
                "description": "Gas Station",
                "amount_range": (-80, -30),
                "frequency": 0.1,
            },
            {
                "description": "Online Shopping",
                "amount_range": (-200, -25),
                "frequency": 0.15,
            },
            {
                "description": "Restaurant",
                "amount_range": (-60, -15),
                "frequency": 0.15,
            },
            {"description": "Salary", "amount_range": (2500, 5000), "frequency": 0.02},
            {
                "description": "ATM Withdrawal",
                "amount_range": (-200, -20),
                "frequency": 0.05,
            },
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

    def ensure_database_dir(self):
        """Ensure database directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def create_tables(self):
        """Create database tables using the shared repository schema."""
        path_manager.set_database_path(self.db_path)
        ensure_tables()

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
        base_date = datetime.now() - timedelta(days=90)

        for i in range(num_accounts):
            institution = random.choice(self.institutions)
            account_id = f"account-{i + 1:03d}-{random.randint(1000, 9999)}"

            account = {
                "id": account_id,
                "institution_id": institution["id"],
                "status": "READY",
                "iban": self.generate_iban(institution["country"]),
                "name": f"Personal Account {i + 1}",
                "currency": "EUR",
                "created": (
                    base_date + timedelta(days=random.randint(0, 30))
                ).isoformat(),
                "last_accessed": (
                    datetime.now() - timedelta(hours=random.randint(1, 48))
                ).isoformat(),
                "last_updated": datetime.now().isoformat(),
            }
            accounts.append(account)

        return accounts

    def generate_transactions(
        self, accounts: list[dict[str, Any]], num_transactions_per_account: int = 50
    ) -> list[dict[str, Any]]:
        """Generate sample transactions for accounts."""
        transactions = []
        base_date = datetime.now() - timedelta(days=60)

        for account in accounts:
            account_transactions = []
            current_balance = random.uniform(500, 3000)

            for i in range(num_transactions_per_account):
                # Choose transaction type based on frequency weights
                transaction_type = random.choices(
                    self.transaction_types,
                    weights=[t["frequency"] for t in self.transaction_types],
                )[0]

                # Generate transaction amount
                min_amount: float
                max_amount: float
                min_amount, max_amount = transaction_type["amount_range"]
                amount = round(random.uniform(min_amount, max_amount), 2)

                # Generate transaction date (more recent transactions are more likely)
                days_ago = random.choices(
                    range(60), weights=[1.5 ** (60 - d) for d in range(60)]
                )[0]
                transaction_date = base_date + timedelta(
                    days=days_ago,
                    hours=random.randint(6, 22),
                    minutes=random.randint(0, 59),
                )

                # Generate transaction IDs
                transaction_id = f"bank-txn-{account['id']}-{i + 1:04d}"
                internal_transaction_id = f"int-txn-{random.randint(100000, 999999)}"

                # Create realistic descriptions
                descriptions: dict[str, list[str]] = {
                    "Grocery Store": [
                        "TESCO",
                        "SAINSBURY'S",
                        "LIDL",
                        "ALDI",
                        "WALMART",
                        "CARREFOUR",
                    ],
                    "Coffee Shop": [
                        "STARBUCKS",
                        "COSTA COFFEE",
                        "PRET A MANGER",
                        "LOCAL CAFE",
                    ],
                    "Gas Station": ["BP", "SHELL", "ESSO", "GALP", "PETROBRAS"],
                    "Online Shopping": ["AMAZON", "EBAY", "ZALANDO", "ASOS", "APPLE"],
                    "Restaurant": [
                        "PIZZA HUT",
                        "MCDONALD'S",
                        "BURGER KING",
                        "LOCAL RESTAURANT",
                    ],
                    "Salary": ["MONTHLY SALARY", "PAYROLL DEPOSIT", "SALARY PAYMENT"],
                    "ATM Withdrawal": ["ATM WITHDRAWAL", "CASH WITHDRAWAL"],
                    "Transfer to Savings": ["SAVINGS TRANSFER", "INVESTMENT TRANSFER"],
                    "Inter-account Transfer": [
                        "TRANSFER TO CHECKING",
                        "TRANSFER FROM SAVINGS",
                        "INTERNAL TRANSFER",
                    ],
                }

                specific_descriptions: list[str] = descriptions.get(
                    transaction_type["description"], [transaction_type["description"]]
                )
                description = random.choice(specific_descriptions)

                # Determine status (most are booked, some recent ones might be pending)
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

                transaction = {
                    "accountId": account["id"],
                    "transactionId": transaction_id,
                    "internalTransactionId": internal_transaction_id,
                    "institutionId": account["institution_id"],
                    "iban": account["iban"],
                    "transactionDate": transaction_date.isoformat(),
                    "description": description,
                    "transactionValue": amount,
                    "transactionCurrency": account["currency"],
                    "transactionStatus": status,
                    "rawTransaction": raw_transaction,
                }

                account_transactions.append(transaction)
                current_balance += amount

            # Sort transactions by date for realistic ordering
            account_transactions.sort(key=lambda x: x["transactionDate"])
            transactions.extend(account_transactions)

        return transactions

    def generate_balances(self, accounts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Generate sample balances for accounts."""
        balances = []

        for account in accounts:
            # Calculate balance from transactions (simplified)
            base_balance = random.uniform(500, 2000)

            balance_types = ["interimAvailable", "closingBooked", "authorised"]

            for balance_type in balance_types:
                # Add some variation to balance types
                variation = (
                    random.uniform(-50, 50) if balance_type != "interimAvailable" else 0
                )
                balance_amount = base_balance + variation

                balance = {
                    "account_id": account["id"],
                    "bank": account["institution_id"],
                    "status": account["status"],
                    "iban": account["iban"],
                    "amount": round(balance_amount, 2),
                    "currency": account["currency"],
                    "type": balance_type,
                    "timestamp": datetime.now().isoformat(),
                }
                balances.append(balance)

        return balances

    def insert_data(
        self,
        accounts: list[dict[str, Any]],
        transactions: list[dict[str, Any]],
        balances: list[dict[str, Any]],
    ):
        """Insert generated data into the database."""
        conn = create_connection(self.db_path)
        cursor = conn.cursor()

        # Insert accounts
        for account in accounts:
            cursor.execute(
                """
                INSERT OR REPLACE INTO accounts
                (id, institution_id, status, iban, name, currency, created, last_accessed, last_updated, display_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    account["id"],
                    account["institution_id"],
                    account["status"],
                    account["iban"],
                    account["name"],
                    account["currency"],
                    account["created"],
                    account["last_accessed"],
                    account["last_updated"],
                    None,  # display_name is initially None for sample data
                ),
            )

        # Insert transactions
        for transaction in transactions:
            cursor.execute(
                """
                INSERT OR REPLACE INTO transactions
                (accountId, transactionId, internalTransactionId, institutionId, iban,
                 transactionDate, description, transactionValue, transactionCurrency,
                 transactionStatus, rawTransaction)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    transaction["accountId"],
                    transaction["transactionId"],
                    transaction["internalTransactionId"],
                    transaction["institutionId"],
                    transaction["iban"],
                    transaction["transactionDate"],
                    transaction["description"],
                    transaction["transactionValue"],
                    transaction["transactionCurrency"],
                    transaction["transactionStatus"],
                    json.dumps(transaction["rawTransaction"]),
                ),
            )

        # Insert balances
        for balance in balances:
            cursor.execute(
                """
                INSERT INTO balances
                (account_id, bank, status, iban, amount, currency, type, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    balance["account_id"],
                    balance["bank"],
                    balance["status"],
                    balance["iban"],
                    balance["amount"],
                    balance["currency"],
                    balance["type"],
                    balance["timestamp"],
                ),
            )

        # Build category name -> id mapping (defaults are seeded by create_tables)
        cursor.execute("SELECT id, name FROM categories")
        category_map = {row[1]: row[0] for row in cursor.fetchall()}

        # Assign categories to ~60% of transactions and learn keywords
        for transaction in transactions:
            if random.random() > 0.6:
                continue

            description = transaction["description"]
            # Find matching category from the description-to-category mapping
            category_name = None
            for desc_key, cat_name in DESCRIPTION_TO_CATEGORY.items():
                if (
                    desc_key.lower() in description.lower()
                    or description.lower() in desc_key.lower()
                ):
                    category_name = cat_name
                    break

            if not category_name or category_name not in category_map:
                continue

            category_id = category_map[category_name]

            cursor.execute(
                "INSERT OR IGNORE INTO transaction_categories (accountId, transactionId, categoryId) VALUES (?, ?, ?)",
                (transaction["accountId"], transaction["transactionId"], category_id),
            )

            # Learn keywords
            keywords = extract_keywords(description)
            for keyword in keywords:
                cursor.execute(
                    """INSERT INTO category_keywords (keyword, categoryId, frequency)
                       VALUES (?, ?, 1)
                       ON CONFLICT(keyword, categoryId) DO UPDATE SET frequency = frequency + 1""",
                    (keyword, category_id),
                )

        conn.commit()
        conn.close()

    def generate_sample_database(
        self, num_accounts: int = 3, num_transactions_per_account: int = 50
    ):
        """Generate complete sample database."""
        click.echo(f"🗄️  Creating sample database at: {self.db_path}")

        self.ensure_database_dir()
        self.create_tables()

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

        # Print summary
        click.echo("\n✅ Sample database created successfully!")
        click.echo("📊 Summary:")
        click.echo(f"   - Accounts: {len(accounts)}")
        click.echo(f"   - Transactions: {len(transactions)}")
        click.echo(f"   - Balances: {len(balances)}")
        click.echo(f"   - Database: {self.db_path}")

        # Show account details
        click.echo("\n📋 Sample accounts:")
        for account in accounts:
            institution_name = next(
                inst["name"]
                for inst in self.institutions
                if inst["id"] == account["institution_id"]
            )
            click.echo(f"   - {account['id']} ({institution_name}) - {account['iban']}")


@click.command()
@click.option(
    "--database",
    type=click.Path(path_type=Path),
    help="Path to database file (default: uses LEGGEN_DATABASE_PATH or ~/.config/leggen/leggen-dev.db)",
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
    import os

    from leggen.utils.paths import path_manager

    # Determine database path
    if database:
        db_path = database
    else:
        # Use development database by default to avoid overwriting production data
        env_path = os.environ.get("LEGGEN_DATABASE_PATH")
        if env_path:
            db_path = Path(env_path)
        else:
            # Default to development database in config directory
            db_path = path_manager.get_config_dir() / "leggen-dev.db"

    # Check if database exists and ask for confirmation
    if db_path.exists():
        if not force:
            click.echo(f"⚠️  Database already exists: {db_path}")
            if not click.confirm("Do you want to overwrite it?"):
                click.echo("Aborted.")
                ctx.exit(0)
        # Truly overwrite: remove the existing database (and any SQLite
        # sidecar files) so no stale rows survive the regeneration.
        for suffix in ("", "-wal", "-shm", "-journal"):
            sidecar = db_path.with_name(db_path.name + suffix)
            sidecar.unlink(missing_ok=True)

    # Generate the sample database
    generator = SampleDataGenerator(db_path)
    generator.generate_sample_database(accounts, transactions)

    # Show usage instructions
    click.echo("\n🚀 Usage instructions:")
    click.echo("To use this sample database with leggen commands:")
    click.echo(f"   export LEGGEN_DATABASE_PATH={db_path}")
    click.echo("   leggen transactions")
    click.echo("")
    click.echo("To use this sample database with leggen server:")
    click.echo(f"   leggen --database {db_path} server")
