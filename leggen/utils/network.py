import click
import requests

from leggen.utils.text import error


def get(ctx: click.Context, path: str, params: dict = {}):
    """
    GET request to the GoCardless API
    """

    url = f"{ctx.obj['api_url']}{path}"
    res = requests.get(url, headers=ctx.obj["headers"], params=params)
    try:
        res.raise_for_status()
    except Exception as e:
        error(f"Error: {e}")
        ctx.abort()
    return res.json()


def post(ctx: click.Context, path: str, data: dict = {}):
    """
    POST request to the GoCardless API
    """

    url = f"{ctx.obj['api_url']}{path}"
    res = requests.post(url, headers=ctx.obj["headers"], json=data)
    try:
        res.raise_for_status()
    except Exception as e:
        error(f"Error: {e}")
        ctx.abort()
    return res.json()


def put(ctx: click.Context, path: str, data: dict = {}):
    """
    PUT request to the GoCardless API
    """

    url = f"{ctx.obj['api_url']}{path}"
    res = requests.put(url, headers=ctx.obj["headers"], json=data)
    try:
        res.raise_for_status()
    except Exception as e:
        error(f"Error: {e}")
        error(res.text)
        ctx.abort()
    return res.json()
