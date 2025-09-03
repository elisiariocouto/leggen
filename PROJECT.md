# Leggen Web Transformation Project

## Overview
Transform leggen from CLI-only to web application with FastAPI backend (`leggend`) and SvelteKit frontend (`leggen-web`).

## Progress Tracking

### ✅ Phase 1: FastAPI Backend (`leggend`)

#### 1.1 Core Structure
- [x] Create directory structure (`leggend/`, `api/`, `services/`, etc.)
- [x] Add FastAPI dependencies to pyproject.toml
- [x] Create configuration management system
- [x] Set up FastAPI main application
- [x] Create Pydantic models for API responses

#### 1.2 API Endpoints
- [x] Banks API (`/api/v1/banks/`)
  - [x] `GET /institutions` - List available banks
  - [x] `POST /connect` - Connect to bank
  - [x] `GET /status` - Bank connection status
- [x] Accounts API (`/api/v1/accounts/`)
  - [x] `GET /` - List all accounts
  - [x] `GET /{id}/balances` - Account balances
  - [x] `GET /{id}/transactions` - Account transactions
- [x] Sync API (`/api/v1/sync/`)
  - [x] `POST /` - Trigger manual sync
  - [x] `GET /status` - Sync status
- [x] Notifications API (`/api/v1/notifications/`)
  - [x] `GET/POST/PUT /settings` - Manage notification settings

#### 1.3 Background Jobs
- [x] Implement APScheduler for sync scheduling
- [x] Replace Ofelia with internal Python scheduler
- [x] Migrate existing sync logic from CLI

### ⏳ Phase 2: SvelteKit Frontend (`leggen-web`)

#### 2.1 Project Setup
- [ ] Create SvelteKit project structure
- [ ] Set up API client for backend communication
- [ ] Design component architecture

#### 2.2 UI Components
- [ ] Dashboard with account overview
- [ ] Bank connection wizard
- [ ] Transaction history and filtering
- [ ] Settings management
- [ ] Real-time sync status

### ✅ Phase 3: CLI Refactoring

#### 3.1 API Client Integration
- [x] Create HTTP client for FastAPI calls
- [x] Refactor existing commands to use APIs
- [x] Maintain CLI user experience
- [x] Add API URL configuration option

### ✅ Phase 4: Docker & Deployment

#### 4.1 Container Setup
- [x] Create Dockerfile for `leggend` service
- [x] Update docker-compose.yml with `leggend` service
- [x] Remove Ofelia dependency (scheduler now internal)
- [ ] Create Dockerfile for `leggen-web` (deferred - not implementing web UI yet)

## Current Status
**Active Phase**: Phase 2 - CLI Integration Complete
**Last Updated**: 2025-09-01
**Completion**: ~80% (FastAPI backend and CLI refactoring complete)

## Next Steps (Future Enhancements)
1. Implement SvelteKit web frontend
2. Add real-time WebSocket support for sync status
3. Implement user authentication and multi-user support
4. Add more comprehensive error handling and logging
5. Implement database migrations for schema changes

## Recent Achievements
- ✅ Complete FastAPI backend with all major endpoints
- ✅ Configurable background job scheduler (replaces Ofelia)
- ✅ CLI successfully refactored to use API endpoints
- ✅ Docker configuration updated for new architecture
- ✅ Maintained backward compatibility and user experience

## Architecture Decisions
- **FastAPI**: For high-performance async API backend
- **APScheduler**: For internal job scheduling (replacing Ofelia)
- **SvelteKit**: For modern, reactive frontend
- **Existing Logic**: Reuse all business logic from current CLI commands
- **Configuration**: Centralize in `leggend` service, maintain TOML compatibility
