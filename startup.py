"""Test"""
import os
import logging
from typing import NoReturn
from dotenv import load_dotenv
from flask import Flask, render_template
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.middleware.dispatcher import DispatcherMiddleware


from flask_apps.flask_app import FlaskApp
from gtfs_loader import FeedLoader, Feed
from helper_functions import instantiate_logger

load_dotenv()
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


def create_default_app(proxies: int = 100) -> Flask:
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
        {
            f"/{key.lower()}": create_app(key).wsgi_app
            for key in os.environ.get("LIST_KEYS").split(",")
        },
    )

    return app


def feed_loader(import_data: bool = False) -> NoReturn:
    """Feed loader."""
    feadloader = FeedLoader(FEED, os.environ.get("LIST_KEYS").split(","))
    if import_data or not os.path.exists(feadloader.feed.db_path):
        feadloader.nightly_import()
    if import_data or not os.path.exists(feadloader.GEOJSON_PATH):
        feadloader.geojson_exports()
    feadloader.scheduler()


if __name__ == "__main__":
    instantiate_logger(logging.getLogger())
    feed_loader()
