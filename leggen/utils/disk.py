import json
import sys
from pathlib import Path

import click

from leggen.utils.text import error, info


def save_file(name: str, d: dict):
    Path.mkdir(Path(click.get_app_dir("leggen")), exist_ok=True)
    config_file = click.get_app_dir("leggen") / Path(name)

    with click.open_file(str(config_file), "w") as f:
        json.dump(d, f)
        info(f"Wrote configuration file at '{config_file}'")


def load_file(name: str) -> dict:
    config_file = click.get_app_dir("leggen") / Path(name)
    try:
        with click.open_file(str(config_file), "r") as f:
            config = json.load(f)
            return config
    except FileNotFoundError:
        error(f"Configuration file '{config_file}' not found")
        sys.exit(1)


def get_prefixed_files(prefix: str) -> list:
    return [
        f.name
        for f in Path(click.get_app_dir("leggen")).iterdir()
        if f.name.startswith(prefix)
    ]
