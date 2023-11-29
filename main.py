"""Main file for the project. Run this to start the server."""
import logging
import os
from threading import Thread
from typing import NoReturn

from flask import Flask, jsonify, render_template
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.middleware.proxy_fix import ProxyFix

from gtfs_loader import FeedLoader

KEY_DICT: dict[str, tuple[str]] = {
    "SUBWAY": ("0", "1"),
    "RAPID_TRANSIT": ("0", "1", "4"),
    "COMMUTER_RAIL": ("2",),
    "BUS": ("3",),
    "FERRY": ("4",),
    "ALL_ROUTES": ("0", "1", "2", "3", "4"),
}
FEED_LOADER = FeedLoader("https://cdn.mbta.com/MBTA_GTFS.zip", KEY_DICT)


def create_app(key: str, proxies: int = 5) -> Flask:
    """Create app for a given key

    Args:
        key (str, optional): Key for the app. Defaults to None.
        proxies (int, optional): Number of proxies to allow on connection, default 10.
    Returns:
        Flask: app for the key."""
    _app = Flask(__name__)

    @_app.route("/")
    def render_map() -> str:
        """Returns map.html."""
        return render_template("map.html")

    @_app.route("/vehicles")
    def get_vehicles() -> str:
        """Returns vehicles as geojson."""
        return jsonify(FEED_LOADER.get_vehicles_feature(key, KEY_DICT[key]))

    @_app.teardown_appcontext
    def shutdown_session(exception=None) -> None:
        """Tears down database session."""
        FEED_LOADER.scoped_session.remove()
        if exception:
            logging.error(exception)

    if proxies:
        _app.wsgi_app = ProxyFix(
            _app.wsgi_app,
            x_for=proxies,
            x_proto=proxies,
            x_host=proxies,
            x_prefix=proxies,
        )
    return _app


def create_default_app(proxies: int = 5) -> Flask:
    """Creates the default Flask object

    Args:
        proxies (int, optional): Number of proxies to allow on connection, default 10.
    Returns:
        Flask: default app.
    """

    _app = Flask(__name__)

    @_app.route("/")
    def index():
        """Returns index.html."""
        return render_template("index.html")

    if proxies:
        _app.wsgi_app = ProxyFix(
            _app.wsgi_app,
            x_for=proxies,
            x_proto=proxies,
            x_host=proxies,
            x_prefix=proxies,
        )
    _app.wsgi_app = DispatcherMiddleware(
        _app.wsgi_app,
        {f"/{key.lower()}": create_app(key).wsgi_app for key in KEY_DICT},
    )

    return _app


def feed_loader(import_data: bool = False) -> NoReturn:
    """Feed loader.

    Args:
        import_data (bool, optional): Whether to import data. Defaults to False.
    """

    if import_data or not os.path.exists(FEED_LOADER.db_path):
        FEED_LOADER.nightly_import()
    if import_data or not os.path.exists(FEED_LOADER.GEOJSON_PATH):
        FEED_LOADER.geojson_exports()
    FEED_LOADER.run()


def run_dev_server(_app: Flask, *args, **kwargs) -> None:
    """Runs the dev server. Doesn't work with 3.12

    Args:
        app (Flask): Flask app.
        kwargs: Keyword arguments for app.run.
    """

    for thread in (
        Thread(target=feed_loader),
        Thread(target=_app.run, *args, kwargs=kwargs),
    ):
        thread.start()
        thread.join()


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    feed_loader()
