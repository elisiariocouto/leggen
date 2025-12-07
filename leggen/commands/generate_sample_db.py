"""Generate sample database command."""

import json
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import click


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

        self.transaction_types = [
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
        ]

    def ensure_database_dir(self):
        """Ensure database directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def create_tables(self):
        """Create database tables."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Create accounts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY,
                institution_id TEXT,
                status TEXT,
                iban TEXT,
                name TEXT,
                currency TEXT,
                created DATETIME,
                last_accessed DATETIME,
                last_updated DATETIME,
                display_name TEXT
            )
        """)

        # Create transactions table with composite primary key
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                accountId TEXT NOT NULL,
                transactionId TEXT NOT NULL,
                internalTransactionId TEXT,
                institutionId TEXT,
                iban TEXT,
                transactionDate DATETIME,
                description TEXT,
                transactionValue REAL,
                transactionCurrency TEXT,
                transactionStatus TEXT,
                rawTransaction JSON,
                PRIMARY KEY (accountId, transactionId)
            )
        """)

        # Create balances table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS balances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT,
                bank TEXT,
                status TEXT,
                iban TEXT,
                amount REAL,
                currency TEXT,
                type TEXT,
                timestamp DATETIME
            )
        """)

        # Create indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_transactions_internal_id ON transactions(internalTransactionId)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transactionDate)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_transactions_account_date ON transactions(accountId, transactionDate)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_transactions_amount ON transactions(transactionValue)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_balances_account_id ON balances(account_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_balances_timestamp ON balances(timestamp)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_balances_account_type_timestamp ON balances(account_id, type, timestamp)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_accounts_institution_id ON accounts(institution_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_accounts_status ON accounts(status)"
        )

        conn.commit()
        conn.close()

    def generate_iban(self, country_code: str) -> str:
        """Generate a realistic IBAN for the given country."""
        ibans = {
            "LT": lambda: f"LT{random.randint(10, 99)}{random.randint(10000, 99999)}{random.randint(10000000, 99999999)}",
            "PT": lambda: f"PT{random.randint(10, 99)}{random.randint(1000, 9999)}{random.randint(1000, 9999)}{random.randint(10000000000, 99999999999)}",
            "GB": lambda: f"GB{random.randint(10, 99)}MONZ{random.randint(100000, 999999)}{random.randint(100000, 999999)}",
            "BR": lambda: f"BR{random.randint(10, 99)}{random.randint(10000000, 99999999)}{random.randint(1000, 9999)}{random.randint(10000000, 99999999)}",
        }
        return ibans.get(
            country_code,
            lambda: f"{country_code}{random.randint(1000000000000000, 9999999999999999)}",
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
                descriptions = {
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
                }

                specific_descriptions = descriptions.get(
                    transaction_type["description"], [transaction_type["description"]]
                )
                description = random.choice(specific_descriptions)

                # Create raw transaction (simplified GoCardless format)
                raw_transaction = {
                    "transactionId": transaction_id,
                    "bookingDate": transaction_date.strftime("%Y-%m-%d"),
                    "valueDate": transaction_date.strftime("%Y-%m-%d"),
                    "transactionAmount": {
                        "amount": str(amount),
                        "currency": account["currency"],
                    },
                    "remittanceInformationUnstructured": description,
                    "bankTransactionCode": "PMNT" if amount < 0 else "RCDT",
                }

                # Determine status (most are booked, some recent ones might be pending)
                status = (
                    "pending" if days_ago < 2 and random.random() < 0.1 else "booked"
                )

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
        conn = sqlite3.connect(str(self.db_path))
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

    from leggen.utils import paths

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
            db_path = paths.get_config_dir() / "leggen-dev.db"

    # Check if database exists and ask for confirmation
    if db_path.exists() and not force:
        click.echo(f"⚠️  Database already exists: {db_path}")
        if not click.confirm("Do you want to overwrite it?"):
            click.echo("Aborted.")
            ctx.exit(0)

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
    click.echo(f"   leggen server --database {db_path}")
