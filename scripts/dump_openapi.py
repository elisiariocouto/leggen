#!/usr/bin/env python
"""Dump the API's OpenAPI schema to openapi.json for frontend type generation.

Run via `just generate-api` (or directly with `uv run python
scripts/dump_openapi.py`) whenever the API models change, then regenerate
the TypeScript types with `npm run generate:api` in frontend/. CI fails if
the committed schema or generated types are stale.
"""

import json
from pathlib import Path

from leggen.commands.server import create_app


def main() -> None:
    schema = create_app().openapi()
    # The real version tracks CalVer releases; pinning it keeps the committed
    # schema from going stale on every release bump.
    schema["info"]["version"] = "dev"
    output_path = Path(__file__).resolve().parent.parent / "openapi.json"
    output_path.write_text(json.dumps(schema, indent=2) + "\n")


if __name__ == "__main__":
    main()
