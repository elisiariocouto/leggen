# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Leggen is an Open Banking CLI tool built in Python that connects to banks using the GoCardless Open Banking API. It allows users to sync bank transactions to SQLite/MongoDB databases, visualize data with NocoDB, and send notifications based on transaction filters.

## Development Commands

- **Install dependencies**: `uv sync` (uses uv package manager)
- **Run locally**: `uv run leggen --help`
- **Lint code**: `ruff check` and `ruff format` (configured in pyproject.toml)
- **Build Docker image**: `docker build -t leggen .`
- **Run with Docker Compose**: `docker compose up -d`

## Architecture

### Core Structure
- `leggen/main.py` - Main CLI entry point using Click framework with custom command loading
- `leggen/commands/` - CLI command implementations (balances, sync, transactions, etc.)
- `leggen/utils/` - Core utilities for authentication, database operations, network requests, and notifications
- `leggen/database/` - Database adapters for SQLite and MongoDB
- `leggen/notifications/` - Discord and Telegram notification handlers

### Key Components

**Configuration System**:
- Uses TOML configuration files (default: `~/.config/leggen/config.toml`)
- Configuration loaded via `leggen/utils/config.py`
- Supports GoCardless API credentials, database settings, and notification configurations

**Authentication & API**:
- GoCardless Open Banking API integration in `leggen/utils/gocardless.py`
- Token-based authentication via `leggen/utils/auth.py`
- Network utilities in `leggen/utils/network.py`

**Database Operations**:
- Dual database support: SQLite (`database/sqlite.py`) and MongoDB (`database/mongo.py`)
- Transaction persistence and balance tracking via `utils/database.py`
- Data storage patterns follow bank account and transaction models

**Command Architecture**:
- Dynamic command loading system in `main.py` with support for command groups
- Commands organized as modules with individual click decorators
- Bank management commands grouped under `commands/bank/`

### Data Flow
1. Configuration loaded from TOML file
2. GoCardless API authentication and bank requisition management
3. Account and transaction data retrieval from banks
4. Data persistence to configured databases (SQLite/MongoDB)
5. Optional notifications sent via Discord/Telegram based on filters
6. Data visualization available through NocoDB integration

## Docker & Deployment

The project uses multi-stage Docker builds with uv for dependency management. The compose.yml includes:
- Main leggen service with sync scheduling via Ofelia
- NocoDB for data visualization
- Optional MongoDB with mongo-express admin interface

## Configuration Requirements

All operations require a valid `config.toml` file with GoCardless API credentials. The configuration structure includes sections for:
- `[gocardless]` - API credentials and endpoint
- `[database]` - Storage backend selection
- `[notifications]` - Discord/Telegram webhook settings
- `[filters]` - Transaction matching patterns for notifications