# 💲 leggen

An Open Banking CLI and API service for managing bank connections and transactions.

This tool provides both a **FastAPI backend service** (`leggend`) and a **command-line interface** (`leggen`) to connect to banks using the GoCardless Open Banking API.

**New in v0.6.11**: Web-ready architecture with FastAPI backend, enhanced CLI, and background job scheduling.

Having your bank data accessible through both CLI and REST API gives you the power to backup, analyze, create reports, and integrate with other applications.

## 🛠️ Technologies

  ### 🔌 API & Backend
  - [FastAPI](https://fastapi.tiangolo.com/): High-performance async API backend (`leggend` service)
  - [GoCardless Open Banking API](https://developer.gocardless.com/bank-account-data/overview): for connecting to banks
  - [APScheduler](https://apscheduler.readthedocs.io/): Background job scheduling with configurable cron

  ### 📦 Storage
  - [SQLite](https://www.sqlite.org): for storing transactions, simple and easy to use
  - [MongoDB](https://www.mongodb.com/docs/): alternative store for transactions, good balance between performance and query capabilities

  ### 📊 Visualization
  - [NocoDB](https://github.com/nocodb/nocodb): for visualizing and querying transactions, a simple and easy to use interface for SQLite

## ✨ Features

### 🎯 Core Banking Features
- Connect to banks using GoCardless Open Banking API (30+ EU countries)
- List all connected banks and their connection statuses
- View balances of all connected accounts
- List and filter transactions across all accounts
- Support for both booked and pending transactions

### 🔄 Data Management
- Sync all transactions with SQLite and/or MongoDB databases
- Background sync scheduling with configurable cron expressions
- Automatic transaction deduplication and status tracking
- Real-time sync status monitoring

### 📡 API & Integration
- **REST API**: Complete FastAPI backend with comprehensive endpoints
- **CLI Interface**: Enhanced command-line tools with new options
- **Health Checks**: Service monitoring and dependency management
- **Auto-reload**: Development mode with file watching

### 🔔 Notifications & Monitoring
- Discord and Telegram notifications for filtered transactions
- Configurable transaction filters (case-sensitive/insensitive)
- Account expiry notifications and status alerts
- Comprehensive logging and error handling

### 📊 Visualization & Analysis
- NocoDB integration for visual data exploration
- Transaction statistics and reporting
- Account balance tracking over time
- Export capabilities for further analysis

## 🚀 Quick Start

### Prerequisites
1. Create a GoCardless account at [https://gocardless.com/bank-account-data/](https://gocardless.com/bank-account-data/)
2. Get your API credentials (key and secret)

### Installation Options

#### Option 1: Docker Compose (Recommended)
The easiest way to get started is with Docker Compose:

```bash
# Clone the repository
git clone https://github.com/elisiariocouto/leggen.git
cd leggen

# Create your configuration
mkdir -p leggen && cp config.example.toml leggen/config.toml
# Edit leggen/config.toml with your GoCardless credentials

# Start all services
docker compose up -d
```

#### Option 2: Local Development
For development or local installation:

```bash
# Install with uv (recommended) or pip
uv sync  # or pip install -e .

# Start the API service
uv run leggend --reload  # Development mode with auto-reload

# Use the CLI (in another terminal)
uv run leggen --help
```

### Configuration

Create a configuration file at `~/.config/leggen/config.toml`:

```toml
[gocardless]
key = "your-api-key"
secret = "your-secret-key"
url = "https://bankaccountdata.gocardless.com/api/v2"

[database]
sqlite = true
mongodb = false

# Optional: MongoDB configuration
[database.mongodb]
uri = "mongodb://localhost:27017"

# Optional: Background sync scheduling
[scheduler.sync]
enabled = true
hour = 3      # 3 AM
minute = 0
# cron = "0 3 * * *"  # Alternative: use cron expression

# Optional: Discord notifications
[notifications.discord]
webhook = "https://discord.com/api/webhooks/..."
enabled = true

# Optional: Telegram notifications
[notifications.telegram]
token = "your-bot-token"
chat_id = 12345
enabled = true

# Optional: Transaction filters for notifications
[filters.case-insensitive]
salary = "salary"
bills = "utility"
```

## 📖 Usage

### API Service (`leggend`)

Start the FastAPI backend service:

```bash
# Production mode
leggend

# Development mode with auto-reload
leggend --reload

# Custom host and port
leggend --host 127.0.0.1 --port 8080
```

**API Documentation**: Visit `http://localhost:8000/docs` for interactive API documentation.

### CLI Commands (`leggen`)

#### Basic Commands
```bash
# Check connection status
leggen status

# Connect to a new bank
leggen bank add

# View account balances
leggen balances

# List recent transactions
leggen transactions --limit 20

# View detailed transactions
leggen transactions --full
```

#### Sync Operations
```bash
# Start background sync
leggen sync

# Synchronous sync (wait for completion)
leggen sync --wait

# Force sync (override running sync)
leggen sync --force --wait
```

#### API Integration
```bash
# Use custom API URL
leggen --api-url http://localhost:8080 status

# Set via environment variable
export LEGGEND_API_URL=http://localhost:8080
leggen status
```

### Docker Usage

```bash
# Start all services
docker compose up -d

# Connect to a bank
docker compose run leggen bank add

# Run a sync
docker compose run leggen sync --wait

# Check logs
docker compose logs leggend
```

## 🔌 API Endpoints

The FastAPI backend provides comprehensive REST endpoints:

### Banks & Connections
- `GET /api/v1/banks/institutions?country=PT` - List available banks
- `POST /api/v1/banks/connect` - Create bank connection
- `GET /api/v1/banks/status` - Connection status
- `GET /api/v1/banks/countries` - Supported countries

### Accounts & Balances  
- `GET /api/v1/accounts` - List all accounts
- `GET /api/v1/accounts/{id}` - Account details
- `GET /api/v1/accounts/{id}/balances` - Account balances
- `GET /api/v1/accounts/{id}/transactions` - Account transactions

### Transactions
- `GET /api/v1/transactions` - All transactions with filtering
- `GET /api/v1/transactions/stats` - Transaction statistics

### Sync & Scheduling
- `POST /api/v1/sync` - Trigger background sync
- `POST /api/v1/sync/now` - Synchronous sync
- `GET /api/v1/sync/status` - Sync status
- `GET/PUT /api/v1/sync/scheduler` - Scheduler configuration

### Notifications
- `GET/PUT /api/v1/notifications/settings` - Manage notifications
- `POST /api/v1/notifications/test` - Test notifications

## 🛠️ Development

### Local Development Setup
```bash
# Clone and setup
git clone https://github.com/elisiariocouto/leggen.git
cd leggen

# Install dependencies
uv sync

# Start API service with auto-reload
uv run leggend --reload

# Use CLI commands
uv run leggen status
```

### Code Structure
```
leggen/              # CLI application
├── commands/        # CLI command implementations
├── utils/           # Shared utilities
└── api_client.py    # API client for leggend service

leggend/             # FastAPI backend service  
├── api/             # API routes and models
├── services/        # Business logic
├── background/      # Background job scheduler
└── main.py          # FastAPI application
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## ⚠️ Notes
- This project is in active development
- Web frontend planned for future releases
- GoCardless API rate limits apply
- Some banks may require additional authorization steps
