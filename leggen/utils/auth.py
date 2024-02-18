import json
from pathlib import Path

import click
import requests

from leggen.utils.text import warning


def create_token(config: dict) -> str:
    """
    Create a new token
    """
    res = requests.post(
        f"{config['api_url']}/token/new/",
        json={"secret_id": config["api_key"], "secret_key": config["api_secret"]},
    )
    res.raise_for_status()
    auth = res.json()
    save_auth(auth)
    return auth["access"]


def get_token(config: dict) -> str:
    """
    Get the token from the auth file or request a new one
    """
    auth_file = click.get_app_dir("leggen") / Path("auth.json")
    if auth_file.exists():
        with click.open_file(str(auth_file), "r") as f:
            auth = json.load(f)
        if not auth.get("access"):
            return create_token(config)

        res = requests.post(
            f"{config['api_url']}/token/refresh/", json={"refresh": auth["refresh"]}
        )
        try:
            res.raise_for_status()
            auth.update(res.json())
            save_auth(auth)
            return auth["access"]
        except requests.exceptions.HTTPError:
            warning(
                f"Token probably expired, requesting a new one.\nResponse: {res.status_code}\n{res.text}"
            )
            return create_token(config)
    else:
        return create_token(config)


def save_auth(d: dict):
    Path.mkdir(Path(click.get_app_dir("leggen")), exist_ok=True)
    auth_file = click.get_app_dir("leggen") / Path("auth.json")

    with click.open_file(str(auth_file), "w") as f:
        json.dump(d, f)
