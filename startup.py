"""Test"""
import os
from typing import NoReturn
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from flask_apps import FlaskApp
from gtfs_loader import FeedLoader, Feed

FEED = Feed("https://cdn.mbta.com/MBTA_GTFS.zip")


def create_app(key: str, proxies: int = 10) -> Flask:
    """Create app for a given key

    Args:
        key (str, optional): Key for the app. Defaults to None."""
    app = Flask(__name__)
    flask_app = FlaskApp(app, FEED, key)
    app = flask_app.app
    if proxies:
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=proxies,
            x_proto=proxies,
            x_host=proxies,
            x_prefix=proxies,
        )
    return app


def create_default_app(proxies: int = 10) -> Flask:
    """Creates the default Flask object

    Args:
        proxies (int, optional): Number of proxies to allow on connection, default 10.
    Returns:
        Flask: default app.
    """

    app = Flask(__name__)

    if proxies:
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=proxies,
            x_proto=proxies,
            x_host=proxies,
            x_prefix=proxies,
        )
    app.wsgi_app = DispatcherMiddleware(
        app.wsgi_app,
        {
            f"/{key.lower()}": create_app(key).wsgi_app
            for key in os.environ["LIST_KEYS"].split(",")
        },
    )

    return app


def feed_loader(import_data: bool = False) -> NoReturn:
    """Feed loader."""
    fead_loader = FeedLoader(FEED)
    if import_data or not os.path.exists(fead_loader.feed.db_path):
        fead_loader.nightly_import()
        fead_loader.geojson_exports()
    fead_loader.scheduler()


def set_env(env_dict: dict[str, str] = None) -> None:
    """Set environment variables.

    Args:
        env_dict (dict[str, str], optional): Dictionary of environment variables. Defaults to None.
    """
    env_dict = env_dict or {
        "SUBWAY": "0,1",
        "RAPID_TRANSIT": "0,1,4",
        "COMMUTER_RAIL": "2",
        "BUS": "3",
        "FERRY": "4",
        "ALL_ROUTES": "0,1,2,3,4",
        "LIST_KEYS": "SUBWAY,RAPID_TRANSIT,COMMUTER_RAIL,BUS,FERRY,ALL_ROUTES",
    }
    for key, value in env_dict.items():
        os.environ[key] = value


if __name__ == "__main__":
    feed_loader()
