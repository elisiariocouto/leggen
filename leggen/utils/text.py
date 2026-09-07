import sys
from datetime import datetime

import click
import tabulate


def print_table(data):
    if isinstance(data, list):
        echo(tabulate.tabulate(data, headers="keys"))
    elif isinstance(data, dict):
        echo(tabulate.tabulate([data], headers="keys"))
    else:
        error("Could not create table")


def datefmt(date: str):
    return datetime.fromisoformat(date).strftime("%Y/%m/%d %H:%M")


def echo(msg=""):
    click.echo(msg)
    sys.stdout.flush()


def echo_status(msg, color: str, prefix="> "):
    """Write a status line to stderr, so stdout stays pipeable data.

    Color is left to click, which drops it when stderr is not a terminal;
    forcing it would leak escape codes into pipes and log files.
    """
    padded_msg = "\n".join(f"{prefix}{line}" for line in msg.splitlines())
    click.secho(padded_msg, fg=color, err=True, bold=True)
    sys.stderr.flush()


def success(msg):
    echo_status(msg, "green")


def info(msg):
    echo_status(msg, "blue")


def warning(msg):
    echo_status(msg, "yellow")


def error(msg):
    echo_status(msg, "red")
