import json
from pathlib import Path

import click
import requests

from leggen.utils.text import warning


def create_token(ctx: click.Context) -> str:
    """
    Create a new token
    """
    res = requests.post(
        f"{ctx.obj['gocardless']['url']}/token/new/",
        json={
            "secret_id": ctx.obj["gocardless"]["key"],
            "secret_key": ctx.obj["gocardless"]["secret"],
        },
    )
    res.raise_for_status()
    auth = res.json()
    save_auth(auth)
    return auth["access"]


def get_token(ctx: click.Context) -> str:
    """
    Get the token from the auth file or request a new one
    """
    auth_file = click.get_app_dir("leggen") / Path("auth.json")
    if auth_file.exists():
        with click.open_file(str(auth_file), "r") as f:
            auth = json.load(f)
        if not auth.get("access"):
            return create_token(ctx)

        res = requests.post(
            f"{ctx.obj['gocardless']['url']}/token/refresh/",
            json={"refresh": auth["refresh"]},
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
            return create_token(ctx)
    else:
        return create_token(ctx)


def save_auth(d: dict):
    Path.mkdir(Path(click.get_app_dir("leggen")), exist_ok=True)
    auth_file = click.get_app_dir("leggen") / Path("auth.json")

    with click.open_file(str(auth_file), "w") as f:
        json.dump(d, f)
