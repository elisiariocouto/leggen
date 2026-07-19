import os

import click

cmd_folder = os.path.abspath(os.path.dirname(__file__))


class BankGroup(click.Group):
    def list_commands(self, ctx):
        return sorted(
            filename[:-3]
            for filename in os.listdir(cmd_folder)
            if filename.endswith(".py") and not filename.startswith("__init__")
        )

    def get_command(self, ctx, name):
        try:
            mod = __import__(f"leggen.commands.bank.{name}", None, None, [name])
        except ImportError:
            return None
        return getattr(mod, name, None)


@click.group(cls=BankGroup)
def bank():
    """Manage bank connections"""
