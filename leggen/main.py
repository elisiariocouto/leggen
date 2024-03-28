import os
import sys
from gettext import gettext as _
from pathlib import Path

import click

from leggen.utils.auth import get_token
from leggen.utils.config import load_config
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
        try:
            mod = __import__(f"leggen.commands.{name}", None, None, [name])
        except ImportError as e:
            error(f"Can't import command {name}. Exception: {e}")
            return
        return getattr(mod, name)


@click.option(
    "-c",
    "--config",
    type=click.Path(dir_okay=False),
    default=click.get_app_dir("leggen") / Path("config.toml"),
    show_default=True,
    callback=load_config,
    is_eager=True,
    expose_value=False,
    envvar="LEGGEN_CONFIG_FILE",
    show_envvar=True,
    help="Path to TOML configuration file",
)
@click.group(
    cls=Group,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(package_name="leggen")
@click.pass_context
def cli(ctx: click.Context):
    """
    Leggen: An Open Banking CLI
    """

    # Do not require authentication when printing help messages
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        return

    token = get_token(ctx)
    ctx.obj["headers"] = {"Authorization": f"Bearer {token}"}
