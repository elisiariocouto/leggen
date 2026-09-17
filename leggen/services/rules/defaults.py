"""The category rules leggen ships with.

Conservative on purpose: each matches well-known merchant names or
unambiguous words at word boundaries, so a rule fires on "LIDL" but never
on a word that happens to contain it. They exist to make a fresh install
useful and to show what a rule looks like — the user is expected to edit,
disable or delete them, so the seeder never overwrites a table that has
held rules before.
"""

import sqlite3
from typing import Any

from loguru import logger

from leggen.repositories.db import db_exists, get_db_connection

# Ordered by priority. Earlier rules win, which is how "uber eats" lands in
# Dining before "uber" can land it in Transport, and "galp energia" in
# Utilities before "galp" in Transport.
DEFAULT_CATEGORY_RULES: list[dict[str, Any]] = [
    {
        "name": "Salary",
        "category": "Salary",
        "priority": 10,
        "description": "Incoming payments described as salary or payroll.",
        "lua_script": (
            "return tx.is_income and matches(tx.description,\n"
            '    "\\\\b(salary|salario|salário|vencimento|ordenado|payroll|wages|nómina|nomina|gehalt|lohn)\\\\b")'
        ),
    },
    {
        "name": "Cash withdrawals",
        "category": "Cash",
        "priority": 20,
        "description": "ATM and counter withdrawals.",
        "lua_script": (
            "return tx.is_expense and matches(tx.description,\n"
            '    "\\\\b(atm|levantamento|multibanco|cash withdrawal|withdrawal|geldautomat|retrait)\\\\b")'
        ),
    },
    {
        "name": "Transfers between own accounts",
        "category": "Inter-account",
        "priority": 30,
        "description": (
            "The other side of the transfer is one of the accounts connected to "
            "leggen, or the description says so. Inter-account is excluded from "
            "statistics by default."
        ),
        # Only the counterparty side is tested: for an expense the debtor is
        # the user's own account, so checking both sides matched everything.
        "lua_script": (
            "local other = tx.is_expense and tx.raw.creditor_account or tx.raw.debtor_account\n"
            "local iban = other and other.iban\n"
            "if iban ~= nil and not exact(iban, tx.iban) and is_own_iban(iban) then return true end\n"
            "return matches(tx.description,\n"
            '    "\\\\b(internal transfer|transfer (to|from) (checking|savings|current)|own account|conta pr[oó]pria)\\\\b")'
        ),
    },
    {
        "name": "Savings and investments",
        "category": "Transfer",
        "priority": 35,
        "description": "Money moved into savings or investment products.",
        "lua_script": (
            "return matches(tx.description,\n"
            '    "\\\\b(savings transfer|investment transfer|poupan[cç]a|investimento|trade republic|degiro|etoro)\\\\b")'
        ),
    },
    {
        "name": "Restaurants and food delivery",
        "category": "Dining",
        "priority": 40,
        "description": "Restaurants, cafés, fast food and delivery platforms.",
        "lua_script": (
            "return tx.is_expense and matches(tx.merchant,\n"
            '    "\\\\b(uber eats|glovo|bolt food|deliveroo|just eat|takeaway|mcdonald|burger king|kfc|pizza hut|domino|subway|telepizza|starbucks|costa coffee|pret a manger|caf[eé]|coffee|restaurant|restaurante|pizzeria|pizzaria|bistro|tasca|padaria|pastelaria)\\\\b")'
        ),
    },
    {
        "name": "Supermarkets",
        "category": "Groceries",
        "priority": 50,
        "description": "Supermarket chains and grocery stores.",
        "lua_script": (
            "return tx.is_expense and matches(tx.merchant,\n"
            '    "\\\\b(pingo doce|continente|lidl|aldi|mercadona|auchan|intermarch[eé]|minipre[cç]o|carrefour|tesco|sainsbury|waitrose|asda|morrisons|walmart|rewe|edeka|albert heijn|grocery|supermercado|supermarket|mercado|froiz)\\\\b")'
        ),
    },
    {
        "name": "Utilities",
        "category": "Utilities",
        "priority": 55,
        "description": "Energy, water and telecom providers.",
        "lua_script": (
            "return tx.is_expense and matches(tx.merchant,\n"
            '    "\\\\b(edp|galp energia|endesa|iberdrola|goldenergy|epal|[aá]guas de|meo|vodafone|british gas|edf|octopus energy|thames water|electricity|water bill|gas bill)\\\\b")'
        ),
    },
    {
        "name": "Fuel and transport",
        "category": "Transport",
        "priority": 60,
        "description": "Fuel stations, ride hailing, public transport, tolls and parking.",
        "lua_script": (
            "return tx.is_expense and matches(tx.merchant,\n"
            '    "\\\\b(galp|repsol|cepsa|shell|esso|bp|petrobras|prio|uber|bolt|cabify|via verde|carris|metropolitano|comboios|flixbus|ryanair|easyjet|gas station|fuel|petrol|parking|estacionamento)\\\\b")'
        ),
    },
    {
        "name": "Streaming and subscriptions",
        "category": "Subscriptions",
        "priority": 65,
        "description": "Streaming, cloud and software subscriptions.",
        "lua_script": (
            "return tx.is_expense and matches(tx.merchant,\n"
            '    "\\\\b(netflix|spotify|disney|hbo|youtube premium|apple music|icloud|google one|dropbox|adobe|microsoft 365|office 365|playstation|xbox|nintendo|audible|kindle unlimited|patreon)\\\\b")'
        ),
    },
    {
        "name": "Online shopping",
        "category": "Shopping",
        "priority": 70,
        "description": "Marketplaces and retail brands.",
        "lua_script": (
            "return tx.is_expense and matches(tx.merchant,\n"
            '    "\\\\b(amazon|ebay|zalando|asos|aliexpress|shein|temu|apple|ikea|decathlon|fnac|worten|el corte ingl[eé]s|zara|primark)\\\\b")'
        ),
    },
]


def _never_had_rules(cursor: sqlite3.Cursor) -> bool:
    """True when no rule has ever been inserted.

    An empty table is not enough: a user who deleted every rule must not
    get them back on the next start. category_rules is AUTOINCREMENT, so
    SQLite records its highest ever rowid in sqlite_sequence — absent until
    the first insert.
    """
    if cursor.execute("SELECT COUNT(*) FROM category_rules").fetchone()[0]:
        return False
    row = cursor.execute(
        "SELECT seq FROM sqlite_sequence WHERE name = 'category_rules'"
    ).fetchone()
    return row is None or not row[0]


def seed_default_category_rules() -> int:
    """Insert the builtin rules into a database that has never had any.

    Returns how many were inserted; 0 when the table has ever held a rule.
    A rule whose category is missing is skipped with a warning rather than
    failing the seed.
    """
    if not db_exists():
        return 0
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if not _never_had_rules(cursor):
            return 0
        categories = {
            name: category_id
            for category_id, name in cursor.execute("SELECT id, name FROM categories")
        }
        inserted = 0
        for rule in DEFAULT_CATEGORY_RULES:
            category_id = categories.get(rule["category"])
            if category_id is None:
                logger.warning(
                    f"Builtin rule '{rule['name']}' skipped: category "
                    f"'{rule['category']}' does not exist"
                )
                continue
            cursor.execute(
                """INSERT INTO category_rules
                   (name, description, categoryId, lua_script, priority, is_active, is_default)
                   VALUES (?, ?, ?, ?, ?, 1, 1)""",
                (
                    rule["name"],
                    rule["description"],
                    category_id,
                    rule["lua_script"],
                    rule["priority"],
                ),
            )
            inserted += 1
        conn.commit()
        return inserted
