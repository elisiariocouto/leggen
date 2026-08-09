# Development commands for leggen. Run `just` to list recipes.

set quiet

default:
    just --list

# Start the API server with the local test database and config
server:
    LEGGEN_DATABASE_PATH=./test-data.db LEGGEN_CONFIG_FILE=./config.toml uv run leggen server --reload

# Start the frontend dev server (http://localhost:5173)
frontend:
    cd frontend && npm install && npm run dev

# Generate a mock database at ./test-data.db
seed accounts="5" transactions="100":
    uv run leggen --config config.toml generate_sample_db --database ./test-data.db --accounts {{accounts}} --transactions {{transactions}} --force

# Run all backend checks (ruff, mypy, hooks) and frontend lint
check:
    uv run pre-commit run --all-files
    cd frontend && npm run lint

# Run the backend test suite; pass extra pytest args after --
test *args:
    uv run pytest {{args}}

# Build the frontend for production
build:
    cd frontend && npm run build

# Cut a release (CalVer bump, changelog, tag)
release:
    ./scripts/release.sh
