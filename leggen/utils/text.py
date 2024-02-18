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


def echo_error(msg, color: str, prefix="> ", bold=True, nl=True):
    padded_msg = "\n".join(f"{prefix}{line}" for line in msg.splitlines())
    click.secho(f"{padded_msg}", fg=color, err=True, color=True, bold=True)
    sys.stderr.flush()


def success(msg):
    echo_error(msg, "green")


def info(msg):
    echo_error(msg, "blue")


def warning(msg):
    echo_error(msg, "yellow")


def error(msg):
    echo_error(msg, "red")
