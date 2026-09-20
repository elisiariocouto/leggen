import os

import click
import uvicorn

from leggen.api.app import create_app


@click.command()
@click.option(
    "--reload",
    is_flag=True,
    help="Enable auto-reload for development",
)
@click.option(
    "--host",
    default="0.0.0.0",
    help="Host to bind to (default: 0.0.0.0)",
)
@click.option(
    "--port",
    type=int,
    default=8000,
    help="Port to bind to (default: 8000)",
)
@click.pass_context
def server(ctx: click.Context, reload: bool, host: str, port: int):
    """Start the Leggen API server"""
    log_level = ctx.obj.get("log_level", "info") if ctx.obj else "info"

    if reload:
        # The global path options were applied to this process by the CLI
        # group, but the reload worker is a fresh process where only the
        # environment survives, so they are exported to reach it.
        params = ctx.parent.params if ctx.parent else {}
        for option, variable in (
            ("config", "LEGGEN_CONFIG_FILE"),
            ("config_dir", "LEGGEN_CONFIG_DIR"),
            ("database", "LEGGEN_DATABASE_PATH"),
        ):
            if params.get(option):
                os.environ[variable] = str(params[option])

        # Use string import for reload to work properly
        uvicorn.run(
            "leggen.api.app:create_app",
            factory=True,
            host=host,
            port=port,
            log_level=log_level,
            access_log=True,
            reload=True,
            reload_dirs=["leggen"],  # Watch leggen directory
        )
    else:
        uvicorn.run(
            create_app(),
            host=host,
            port=port,
            log_level=log_level,
            access_log=True,
        )
