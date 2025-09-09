# Agent Guidelines for Leggen

## Build/Lint/Test Commands

### Frontend (React/TypeScript)
- **Dev server**: `cd frontend && npm run dev`
- **Build**: `cd frontend && npm run build`
- **Lint**: `cd frontend && npm run lint`

### Backend (Python)
- **Lint**: `uv run ruff check .`
- **Format**: `uv run ruff format .`
- **Type check**: `uv run mypy leggen leggend --check-untyped-defs`
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
- **Icons**: lucide-react with consistent naming
- **Data fetching**: @tanstack/react-query with proper error handling
- **Components**: Functional components with hooks, proper TypeScript typing

### General
- **Formatting**: ruff for Python, ESLint for TypeScript
- **Commits**: Use conventional commits, run pre-commit hooks before pushing
- **Security**: Never log sensitive data, use environment variables for secrets
