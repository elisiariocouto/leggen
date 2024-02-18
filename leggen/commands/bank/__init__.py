import os

import click

from leggen.main import cli

cmd_folder = os.path.abspath(os.path.dirname(__file__))


class BankGroup(click.Group):
    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(cmd_folder):
            if filename.endswith(".py") and not filename.startswith("__init__"):
                if filename == "list_banks.py":
                    rv.append("list")
                else:
                    rv.append(filename[:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        try:
            if name == "list":
                name = "list_banks"
            mod = __import__(f"leggen.commands.bank.{name}", None, None, [name])
        except ImportError:
            return
        return getattr(mod, name)


@cli.group(cls=BankGroup)
@click.pass_context
def bank(ctx):
    """Manage banks connections"""
    return
