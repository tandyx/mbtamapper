"""Main file for the project. Run this to start the server."""
import argparse
import logging
import os
from threading import Thread
from typing import Any, NoReturn

from flask import Flask, jsonify, render_template
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.middleware.proxy_fix import ProxyFix

from gtfs_loader import Feed, FeedLoader

PARSER = argparse.ArgumentParser()
FEED = Feed("https://cdn.mbta.com/MBTA_GTFS.zip")
KEY_DICT: dict[str, tuple[str]] = {
    "SUBWAY": ("0", "1"),
    "RAPID_TRANSIT": ("0", "1", "4"),
    "COMMUTER_RAIL": ("2",),
    "BUS": ("3",),
    "FERRY": ("4",),
    "ALL_ROUTES": ("0", "1", "2", "3", "4"),
}


# pylint: disable=unused-argument
def add_arg(arg: str, *args, **kwargs) -> Any:
    """Add arguments to the argument parser.

    Args:
        arg (str): The name of the argument to add.
    """
    PARSER.add_argument(f"--{arg}", *args, **kwargs)
    arg_result = getattr(PARSER.parse_args(), arg)
    logging.info("Argument %s set to %s", arg, arg_result)
    return arg_result


def create_app(key: str, proxies: int = 5) -> Flask:
    """Create app for a given key

    Args:
        key (str, optional): Key for the app. Defaults to None.
        proxies (int, optional): Number of proxies to allow on connection, default 10.
    Returns:
        Flask: app for the key."""
    app = Flask(__name__)

    @app.route("/")
    def render_map() -> str:
        """Returns map.html."""
        return render_template("map.html")

    @app.route("/vehicles")
    def get_vehicles() -> str:
        """Returns vehicles as geojson."""

        return jsonify(FEED.get_vehicles(key, KEY_DICT[key]))

    @app.teardown_appcontext
    def shutdown_session(self, exception=None) -> None:
        """Tears down database session."""
        FEED.scoped_session.remove()

    if proxies:
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=proxies,
            x_proto=proxies,
            x_host=proxies,
            x_prefix=proxies,
        )
    return app


def create_default_app(proxies: int = 5) -> Flask:
    """Creates the default Flask object

    Args:
        proxies (int, optional): Number of proxies to allow on connection, default 10.
    Returns:
        Flask: default app.
    """

    app = Flask(__name__)

    @app.route("/")
    def index():
        """Returns index.html."""
        return render_template("index.html")

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
        {f"/{key.lower()}": create_app(key).wsgi_app for key in KEY_DICT},
    )

    return app


def feed_loader(import_data: bool = False) -> NoReturn:
    """Feed loader.

    Args:
        import_data (bool, optional): Whether to import data. Defaults to False.
    """
    feadloader = FeedLoader(FEED, KEY_DICT)
    if import_data or not os.path.exists(feadloader.feed.db_path):
        feadloader.nightly_import()
    if import_data or not os.path.exists(feadloader.GEOJSON_PATH):
        feadloader.geojson_exports()
    feadloader.run()


def run_dev_server(app: Flask, *args, **kwargs) -> None:
    """Runs the dev server. Doesn't work with 3.12

    Args:
        app (Flask): Flask app.
        kwargs: Keyword arguments for app.run.
    """

    for thread in (
        Thread(target=feed_loader),
        Thread(target=app.run, *args, kwargs=kwargs),
    ):
        thread.start()
        thread.join()


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    feed_loader(
        import_data=add_arg(
            "import_data",
            help="Whether to import data and create geojsons. Defaults to False.",
            action=argparse.BooleanOptionalAction,
            default=False,
        )
    )
