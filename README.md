# 💲 leggen

An Open Banking CLI and API service for managing bank connections and transactions.

This tool provides a **unified command-line interface** (`leggen`) with both CLI commands and an integrated **FastAPI backend service**, plus a **React Web Interface** to connect to banks using the GoCardless Open Banking API.

Having your bank data accessible through both CLI and REST API gives you the power to backup, analyze, create reports, and integrate with other applications.

## 🛠️ Technologies

  ### 🔌 API & Backend
  - [FastAPI](https://fastapi.tiangolo.com/): High-performance async API backend (integrated into `leggen server`)
  - [GoCardless Open Banking API](https://developer.gocardless.com/bank-account-data/overview): for connecting to banks
  - [APScheduler](https://apscheduler.readthedocs.io/): Background job scheduling with configurable cron

  ### 📦 Storage
  - [SQLite](https://www.sqlite.org): for storing transactions, simple and easy to use

  ### Frontend
  - [React](https://reactjs.org/): Modern web interface with TypeScript
  - [Vite](https://vitejs.dev/): Fast build tool and development server
  - [Tailwind CSS](https://tailwindcss.com/): Utility-first CSS framework
  - [shadcn/ui](https://ui.shadcn.com/): Modern component system built on Radix UI
  - [TanStack Query](https://tanstack.com/query): Powerful data synchronization for React

## ✨ Features

### 🎯 Core Banking Features
- Connect to banks using GoCardless Open Banking API (30+ EU countries)
- List all connected banks and their connection statuses
- View balances of all connected accounts
- List and filter transactions across all accounts
- Support for both booked and pending transactions

### 🔄 Data Management
- Sync all transactions with SQLite database
- Background sync scheduling with configurable cron expressions
- Automatic transaction deduplication and status tracking
- Real-time sync status monitoring

### 📡 API & Integration
- **REST API**: Complete FastAPI backend with comprehensive endpoints
- **CLI Interface**: Enhanced command-line tools with new options

### 🔔 Notifications & Monitoring
- Discord and Telegram notifications for filtered transactions
- Configurable transaction filters (case-sensitive/insensitive)
- Account expiry notifications and status alerts
- Comprehensive logging and error handling

## 🚀 Quick Start

### Prerequisites
1. Create a GoCardless account at [https://gocardless.com/bank-account-data/](https://gocardless.com/bank-account-data/)
2. Get your API credentials (key and secret)

### Installation Options

#### Option 1: Docker Compose (Recommended)
The easiest way to get started is with Docker Compose, which includes both the React frontend and FastAPI backend:

```bash
# Clone the repository
git clone https://github.com/elisiariocouto/leggen.git
cd leggen

# Create your configuration
mkdir -p data && cp config.example.toml data/config.toml
# Edit data/config.toml with your GoCardless credentials

# Start all services (frontend + backend)
docker compose up -d

# Access the web interface at http://localhost:3000
# API is available at http://localhost:8000
```

#### Production Deployment

For production deployment using published Docker images:

```bash
# Clone the repository
git clone https://github.com/elisiariocouto/leggen.git
cd leggen

# Create your configuration
mkdir -p data && cp config.example.toml data/config.toml
# Edit data/config.toml with your GoCardless credentials

# Start production services
docker compose up -d

# Access the web interface at http://localhost:3000
# API is available at http://localhost:8000
```

### Development vs Production

- **Development**: Use `docker compose -f compose.dev.yml up -d` (builds from source)
- **Production**: Use `docker compose up -d` (uses published images)

#### Option 2: Local Development
For development or local installation:

```bash
# Install with uv (recommended) or pip
uv sync  # or pip install -e .

# Start the API service
uv run leggen server --reload  # Development mode with auto-reload

# Use the CLI (in another terminal)
uv run leggen --help
```

### Configuration

Create a configuration file at `./data/config.toml` (for Docker) or `~/.config/leggen/config.toml` (for local development):

```toml
[gocardless]
key = "your-api-key"
secret = "your-secret-key"
url = "https://bankaccountdata.gocardless.com/api/v2"

[database]
sqlite = true

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
[filters]
case_insensitive = ["salary", "utility"]
case_sensitive = ["SpecificStore"]
```

## 📖 Usage

### API Service (`leggen server`)

Start the FastAPI backend service:

```bash
# Production mode
leggen server

# Development mode with auto-reload
leggen server --reload

# Custom host and port
leggen server --host 127.0.0.1 --port 8080
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
export LEGGEN_API_URL=http://localhost:8080
leggen status
```

### Docker Usage

#### Development (build from source)
```bash
# Start development services
docker compose -f compose.dev.yml up -d

# View service status
docker compose -f compose.dev.yml ps

# Check logs
docker compose -f compose.dev.yml logs frontend
docker compose -f compose.dev.yml logs leggen-server

# Stop development services
docker compose -f compose.dev.yml down
```

#### Production (use published images)
```bash
# Start production services
docker compose up -d

# View service status
docker compose ps

# Check logs
docker compose logs frontend
docker compose logs leggen-server

# Access the web interface at http://localhost:3000
# API documentation at http://localhost:8000/docs

# Stop production services
docker compose down
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
uv run leggen server --reload

# Use CLI commands
uv run leggen status
```

### Testing

Run the comprehensive test suite with:

```bash
# Run all tests
uv run pytest

# Run unit tests only
uv run pytest tests/unit/

# Run with verbose output
uv run pytest tests/unit/ -v

# Run specific test files
uv run pytest tests/unit/test_config.py -v
uv run pytest tests/unit/test_scheduler.py -v
uv run pytest tests/unit/test_api_banks.py -v

# Run tests by markers
uv run pytest -m unit      # Unit tests
uv run pytest -m api       # API endpoint tests
uv run pytest -m cli       # CLI tests
```

The test suite includes:
- **Configuration management tests** - TOML config loading/saving
- **API endpoint tests** - FastAPI route testing with mocked dependencies
- **CLI API client tests** - HTTP client integration testing
- **Background scheduler tests** - APScheduler job management
- **Mock data and fixtures** - Realistic test data for banks, accounts, transactions

### Code Structure
```
leggen/              # CLI application
├── commands/        # CLI command implementations
├── utils/           # Shared utilities
├── api/             # FastAPI API routes and models
├── services/        # Business logic
├── background/      # Background job scheduler
└── api_client.py    # API client for server communication

tests/               # Test suite
├── conftest.py      # Shared test fixtures
└── unit/            # Unit tests
    ├── test_config.py      # Configuration tests
    ├── test_scheduler.py   # Background scheduler tests
    ├── test_api_banks.py   # Banks API tests
    ├── test_api_accounts.py # Accounts API tests
    └── test_api_client.py  # CLI API client tests
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

The repository uses GitHub Actions for CI/CD:
- **CI**: Runs Python tests (`uv run pytest`) and frontend linting/build on every push
- **Release**: Creates GitHub releases with changelog when tags are pushed

## ⚠️ Notes
- This project is in active development
- GoCardless API rate limits apply
- Some banks may require additional authorization steps
- Docker images are automatically built and published on releases
