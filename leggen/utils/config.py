import sys

import click
import tomllib

from leggen.utils.text import error


def load_config(ctx: click.Context, _, filename):
    try:
        with click.open_file(str(filename), "rb") as f:
            # TODO: Implement configuration file validation (use pydantic?)
            ctx.obj = tomllib.load(f)
    except FileNotFoundError:
        error(
            "Configuration file not found. Provide a valid configuration file path with leggen --config <path> or LEGGEN_CONFIG=<path> environment variable."
        )
        sys.exit(1)
