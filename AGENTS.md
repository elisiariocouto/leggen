# Agent Guidelines for Leggen

## Quick Setup for Development

### Prerequisites
- **uv** must be installed for Python dependency management (can be installed via `pip install uv`)
- **Configuration file**: Copy `config.example.toml` to `config.toml` before running any commands:
  ```bash
  cp config.example.toml config.toml
  ```

### Generate Mock Database
The leggen CLI provides a command to generate a mock database for testing:

```bash
# Generate sample database with default settings (3 accounts, 50 transactions each)
uv run leggen --config config.toml generate_sample_db --database /path/to/test.db --force

# Custom configuration
uv run leggen --config config.toml generate_sample_db --database ./test-data.db --accounts 5 --transactions 100 --force
```

The command outputs instructions for setting the required environment variable to use the generated database.

### Start the API Server
1. Install uv if not already installed: `pip install uv`
2. Set the database environment variable to point to your generated mock database:
   ```bash
   export LEGGEN_DATABASE_PATH=/path/to/your/generated/database.db
   ```
3. Ensure the API can find the configuration file (choose one):
   ```bash
   # Option 1: Copy config to the expected location
   mkdir -p ~/.config/leggen && cp config.toml ~/.config/leggen/config.toml
   
   # Option 2: Set environment variable to current config file
   export LEGGEN_CONFIG_FILE=./config.toml
   ```
4. Start the API server:
   ```bash
   uv run leggen server
   ```
   - For development mode with auto-reload: `uv run leggen server --reload`
   - API will be available at `http://localhost:8000` with docs at `http://localhost:8000/api/v1/docs`

### Start the Frontend
1. Navigate to the frontend directory: `cd frontend`
2. Install npm dependencies: `npm install`
3. Start the development server: `npm run dev`
   - Frontend will be available at `http://localhost:3000`
   - The frontend is configured to connect to the API at `http://localhost:8000/api/v1`

## Build/Lint/Test Commands

### Frontend (React/TypeScript)
- **Dev server**: `cd frontend && npm run dev`
- **Build**: `cd frontend && npm run build`
- **Lint**: `cd frontend && npm run lint`

### Backend (Python)
- **Lint**: `uv run ruff check .`
- **Format**: `uv run ruff format .`
- **Type check**: `uv run mypy leggen --check-untyped-defs`
- **All checks**: `uv run pre-commit run --all-files`
- **Run all tests**: `uv run pytest`
- **Run single test**: `uv run pytest tests/unit/test_api_accounts.py::TestAccountsAPI::test_get_all_accounts_success -v`
- **Run tests by marker**: `uv run pytest -m "api"` or `uv run pytest -m "unit"`

## Code Style Guidelines

### Python
- **Imports**: Standard library → Third-party → Local (blank lines between groups)
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Types**: Use type hints for all function parameters and return values
- **Error handling**: Use specific exceptions, loguru for logging
- **Path handling**: Use `pathlib.Path` instead of `os.path`
- **CLI**: Use Click framework with proper option decorators

### TypeScript/React
- **Imports**: React hooks first, then third-party, then local components/types
- **Naming**: PascalCase for components, camelCase for variables/functions
- **Types**: Use `import type` for type-only imports, define interfaces/types
- **Styling**: Tailwind CSS with `clsx` utility for conditional classes
- **UI Components**: shadcn/ui components for consistent design system
- **Icons**: lucide-react with consistent naming
- **Data fetching**: @tanstack/react-query with proper error handling
- **Components**: Functional components with hooks, proper TypeScript typing

## Frontend Structure

### Layout Architecture
- **Root Layout**: `frontend/src/routes/__root.tsx` - Contains main app structure with Sidebar and Header
- **Header/Navbar**: `frontend/src/components/Header.tsx` - Top navigation bar (sticky on mobile only)
- **Sidebar**: `frontend/src/components/Sidebar.tsx` - Left navigation sidebar
- **Routes**: `frontend/src/routes/` - TanStack Router file-based routing

### Key Components Location
- **UI Components**: `frontend/src/components/ui/` - shadcn/ui components and reusable UI primitives
- **Feature Components**: `frontend/src/components/` - Main app components
- **Pages**: `frontend/src/routes/` - Route components (index.tsx, transactions.tsx, etc.)
- **Hooks**: `frontend/src/hooks/` - Custom React hooks
- **API**: `frontend/src/lib/api.ts` - API client configuration
- **Context**: `frontend/src/contexts/` - React contexts (ThemeContext, etc.)

### Routing Structure
- `/` - Overview/Dashboard (TransactionsTable component)
- `/transactions` - Transactions page
- `/analytics` - Analytics page
- `/notifications` - Notifications page
- `/settings` - Settings page

### General
- **Formatting**: ruff for Python, ESLint for TypeScript
- **Commits**: Use conventional commits with optional scopes, run pre-commit hooks before pushing
  - Format: `type(scope): Description starting with uppercase and ending with period.`
  - Scopes: `cli`, `api`, `frontend` (optional)
  - Types: `feat`, `fix`, `refactor` (avoid too many different types)
  - Examples:
    - `feat(frontend): Add support for S3 backups.`
    - `fix(api): Resolve authentication timeout issues.`
    - `refactor(cli): Improve error handling for missing config.`
  - Avoid including specific numbers, counts, or data-dependent information that may become outdated
- **Security**: Never log sensitive data, use environment variables for secrets

## AI Development Support

### shadcn/ui Integration
This project uses shadcn/ui for consistent UI components. The MCP server is configured for AI agents to:
- Search and browse available shadcn/ui components
- View component implementation details and examples
- Generate proper installation commands for new components

Use the shadcn MCP tools when working with UI components to ensure consistency with the existing design system.

## Contributing Guidelines

This repository follows conventional changelog practices. Refer to `CONTRIBUTING.md` for detailed contribution guidelines including:
- Commit message format and scoping
- Release process using `scripts/release.sh`
- Pre-commit hooks setup with `pre-commit install`
- When the pre-commit fails, the commit is canceled
