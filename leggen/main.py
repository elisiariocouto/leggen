import os
import sys
from gettext import gettext as _
from pathlib import Path

import click
from loguru import logger

from leggen.utils.config import config as config_singleton
from leggen.utils.paths import path_manager
from leggen.utils.text import error

cmd_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "commands"))


class Group(click.Group):
    # Overriden version to support sections
    def format_commands(self, ctx, formatter):
        commands = []
        for subcommand in self.list_commands(ctx):
            if subcommand.startswith("GROUP_"):
                cmd = self.get_command(ctx, subcommand[6:])
            else:
                cmd = self.get_command(ctx, subcommand)
            # What is this, the tool lied about a command.  Ignore it
            if cmd is None:
                continue
            if cmd.hidden:
                continue

            commands.append((subcommand, cmd))

        # allow for 3 times the default spacing
        if len(commands):
            limit = formatter.width - 6 - max(len(cmd[0]) for cmd in commands)

            rows = []
            groups = []
            for subcommand, cmd in commands:
                help = cmd.get_short_help_str(limit)
                if subcommand.startswith("GROUP_"):
                    groups.append((subcommand[6:], help))
                else:
                    rows.append((subcommand, help))

            if groups:
                with formatter.section(_("Command Groups")):
                    formatter.write_dl(groups)

            if rows:
                with formatter.section(_("Commands")):
                    formatter.write_dl(rows)

    def list_commands(self, ctx):
        commands = []
        groups = []
        for filename in os.listdir(cmd_folder):
            if filename.endswith(".py") and not filename.startswith("__init__"):
                commands.append(filename[:-3])
            if not filename.endswith(".py"):
                for group_filename in os.listdir(os.path.join(cmd_folder, filename)):
                    if group_filename == "__init__.py":
                        groups.append(f"GROUP_{filename}")

        commands.sort()
        groups.sort()
        return groups + commands

    def get_command(self, ctx, name):
        name = name.replace("-", "_")
        try:
            mod = __import__(f"leggen.commands.{name}", None, None, [name])
        except ImportError as e:
            error(f"Can't import command {name}. Exception: {e}")
            return
        return getattr(mod, name, None)


@click.option(
    "-c",
    "--config",
    type=click.Path(dir_okay=False),
    default=None,
    envvar="LEGGEN_CONFIG_FILE",
    show_envvar=True,
    help="Path to TOML configuration file (default: <config-dir>/config.toml)",
)
@click.option(
    "--config-dir",
    type=click.Path(exists=False, file_okay=False, path_type=Path),
    envvar="LEGGEN_CONFIG_DIR",
    show_envvar=True,
    help="Directory containing configuration files (default: ~/.config/leggen)",
)
@click.option(
    "--database",
    type=click.Path(dir_okay=False, path_type=Path),
    envvar="LEGGEN_DATABASE_PATH",
    show_envvar=True,
    help="Path to SQLite database file (default: <config-dir>/leggen.db)",
)
@click.option(
    "--api-url",
    type=str,
    default="http://localhost:8000",
    envvar="LEGGEN_API_URL",
    show_envvar=True,
    help="URL of the leggen API service",
)
@click.option(
    "--log-level",
    type=click.Choice(
        ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False
    ),
    default="INFO",
    envvar="LEGGEN_LOG_LEVEL",
    show_envvar=True,
    help="Set the logging level",
)
@click.option(
    "--api-key",
    type=str,
    default=None,
    envvar="LEGGEN_API_KEY",
    show_envvar=True,
    help="API key for authenticating with the leggen server",
)
@click.option(
    "--no-verify-ssl",
    is_flag=True,
    default=False,
    envvar="LEGGEN_NO_VERIFY_SSL",
    show_envvar=True,
    help="Disable SSL certificate verification for API requests",
)
@click.group(
    cls=Group,
    context_settings={
        "help_option_names": ["-h", "--help"],
        "token_normalize_func": lambda x: x.replace("-", "_"),
    },
)
@click.version_option(package_name="leggen")
@click.pass_context
def cli(
    ctx: click.Context,
    config: str | None,
    config_dir: Path,
    database: Path,
    api_url: str,
    api_key: str | None,
    log_level: str,
    no_verify_ssl: bool,
):
    """
    Leggen: An Open Banking CLI
    """

    # Configure loguru log level
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        level=log_level.upper(),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    # Record user-provided paths; nothing is loaded here. The config file is
    # read lazily by the singleton when something actually needs it (the
    # server lifespan or the CLI's api-key fallback), so help output and the
    # bootstrap commands never require one.
    if config_dir:
        path_manager.set_config_dir(config_dir)
    if database:
        path_manager.set_database_path(database)
    if config:
        config_singleton.set_config_path(config)

    # Store CLI options in context for commands to use. The api_key config
    # fallback happens lazily in LeggenAPIClient.from_context.
    ctx.ensure_object(dict)
    ctx.obj["api_url"] = api_url
    ctx.obj["verify_ssl"] = not no_verify_ssl
    ctx.obj["log_level"] = log_level.lower()
    ctx.obj["api_key"] = api_key
