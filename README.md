# 💲 leggen

An Open Banking CLI.

This tool aims to provide a simple way to connect to banks using the GoCardless Open Banking API.

Having a simple CLI tool to connect to banks and list transactions can be very useful for developers and companies that need to access bank data.

Having your bank data in a database, gives you the power to backup, analyze and create reports with your data.

## 🛠️ Technologies
  - Python: for the CLI
  - [GoCardless Open Banking API](https://developer.gocardless.com/bank-account-data/overview): for connecting to banks
  - [MongoDB](https://www.mongodb.com/docs/): for storing transactions, good balance between performance and query capabilities
  - [Ofelia](https://github.com/mcuadros/ofelia): for scheduling regular syncs with the database when using Docker

## ✨ Features
  - Connect to banks using GoCardless Open Banking API
  - List all connected banks and their status
  - List balances of all connected accounts
  - List transactions for an account
  - Sync all transactions with a MongoDB database

## 🚀 Installation and Configuration

In order to use `leggen`, you need to create a GoCardless account. GoCardless is a service that provides access to Open Banking APIs. You can create an account at https://gocardless.com/bank-account-data/.

After creating an account and getting your API keys, the best way is to use the [compose file](docker-compose.yml). Open the file and adapt it to your needs. Then run the following command:

```bash
$ docker compose up -d
```

The leggen container will exit, this is expected. Now you can run the following command to create the configuration file:

```bash
$ docker compose run leggen init
```

Now you need to connect your bank accounts. Run the following command and follow the instructions:

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
  --version   Show the version and exit.
  -h, --help  Show this message and exit.

Command Groups:
  bank  Manage banks connections

Commands:
  balances      List balances of all connected accounts
  init          Create configuration file
  status        List all connected banks and their status
  sync          Sync all transactions with database
  transactions  List transactions for an account
```

## ⚠️ Caveats
  - This project is still in early development.
