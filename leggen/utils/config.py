import json
import sys
from pathlib import Path

import click

from leggen.utils.text import error, info


def save_config(d: dict):
    Path.mkdir(Path(click.get_app_dir("leggen")), exist_ok=True)
    config_file = click.get_app_dir("leggen") / Path("config.json")

    with click.open_file(str(config_file), "w") as f:
        json.dump(d, f)
        info(f"Wrote configuration file at '{config_file}'")


def load_config() -> dict:
    config_file = click.get_app_dir("leggen") / Path("config.json")
    try:
        with click.open_file(str(config_file), "r") as f:
            config = json.load(f)
            return config
    except FileNotFoundError:
        error(
            "Configuration file not found. Run `leggen init` to configure your account."
        )
        sys.exit(1)
