# 💲 leggen

An Open Banking CLI.

This tool aims to provide a simple way to connect to banks using the GoCardless Open Banking API.

Having a simple CLI tool to connect to banks and list transactions can be very useful for developers and companies that need to access bank data.

Having your bank data in a database, gives you the power to backup, analyze and create reports with your data.

## 🛠️ Technologies
  - [GoCardless Open Banking API](https://developer.gocardless.com/bank-account-data/overview): for connecting to banks

  ### 📦 Storage
  - [SQLite](https://www.sqlite.org): for storing transactions, simple and easy to use
  - [MongoDB](https://www.mongodb.com/docs/): alternative store for transactions, good balance between performance and query capabilities

  ### ⏰ Scheduling
  - [Ofelia](https://github.com/mcuadros/ofelia): for scheduling regular syncs with the database when using Docker

  ### 📊 Visualization
  - [NocoDB](https://github.com/nocodb/nocodb): for visualizing and querying transactions, a simple and easy to use interface for SQLite

## ✨ Features
  - Connect to banks using GoCardless Open Banking API
  - List all connected banks and their statuses
  - List balances of all connected accounts
  - List transactions for all connected accounts
  - Sync all transactions with a SQLite or MongoDB database
  - Visualize and query transactions using NocoDB
  - Schedule regular syncs with the database using Ofelia
  - Send notifications to Discrod when transactions match certain filters

## 🚀 Installation and Configuration

In order to use `leggen`, you need to create a GoCardless account. GoCardless is a service that provides access to Open Banking APIs. You can create an account at https://gocardless.com/bank-account-data/.

After creating an account and getting your API keys, the best way is to use the [compose file](docker-compose.yml). Open the file and adapt it to your needs.

### Example Configuration

Create a configuration file at with the following content:

```toml
[gocardless]
key = "your-api-key"
secret = "your-secret-key"
url = "https://bankaccountdata.gocardless.com/api/v2"

[database]
sqlite = true

[notifications.discord]
webhook = "https://discord.com/api/webhooks/..."

[filters]
enabled = true

[filters.case-insensitive]
filter1 = "company-name"
```

### Running Leggen with Docker

After adapting the compose file, run the following command:

```bash
$ docker compose up -d
```

The leggen container will exit, this is expected since you didn't connect any bank accounts yet.

Run the following command and follow the instructions:

```bash
$ docker compose run leggen bank add
```

To sync all transactions with the database, run the following command:

```bash
$ docker compose run leggen sync
```

## 👩‍🏫 Usage

```
$ leggen --help
Usage: leggen [OPTIONS] COMMAND [ARGS]...

  Leggen: An Open Banking CLI

Options:
  --version          Show the version and exit.
  -c, --config FILE  Path to TOML configuration file
                      [env var: LEGGEN_CONFIG_FILE;
                       default: ~/.config/leggen/config.toml]
  -h, --help         Show this message and exit.

Command Groups:
  bank  Manage banks connections

Commands:
  balances      List balances of all connected accounts
  status        List all connected banks and their status
  sync          Sync all transactions with database
  transactions  List transactions
```

## ⚠️ Caveats
  - This project is still in early development, breaking changes may occur.
