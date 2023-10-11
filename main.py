"""Test"""
import os
import time
import logging
from threading import Thread
from typing import NoReturn
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify
from geojson import FeatureCollection
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from sqlalchemy.exc import OperationalError


from gtfs_loader import FeedLoader, Feed, Query

load_dotenv()
FEED = Feed("https://cdn.mbta.com/MBTA_GTFS.zip")
SILVER_LINE_ROUTES = ["741", "742", "743", "751", "749", "746"]

# pylint: disable=unused-argument


def create_app(key: str, proxies: int = 10) -> Flask:
    """Create app for a given key

    Args:
        key (str, optional): Key for the app. Defaults to None.
        proxies (int, optional): Number of proxies to allow on connection, default 10.
    Returns:
        Flask: app for the key."""
    app = Flask(__name__)
    # flask_app = FlaskApp(app, FEED, key)
    # app = flask_app.app

    query = Query(os.environ.get(key).split(","))

    @app.route("/")
    def render_map():
        return render_template("map.html")

    @app.route("/vehicles")
    def get_vehicles():
        sess = FEED.scoped_session()
        add_routes = SILVER_LINE_ROUTES if key == "RAPID_TRANSIT" else ""
        vehicles_query = query.return_vehicles_query(add_routes)
        if key in ["BUS", "ALL_ROUTES"]:
            vehicles_query = vehicles_query.limit(75)
        attempts = 0
        try:
            while attempts <= 10:
                data = sess.execute(vehicles_query).all()
                if data and any(d[0].predictions for d in data):
                    break
                attempts += 1
                time.sleep(1)
        except OperationalError as error:
            data = []
            logging.error("Failed to send data: %s", error)
        if not data:
            logging.error("No data returned in %s attemps", attempts)
        return jsonify(FeatureCollection([v[0].as_feature() for v in data]))

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


def create_default_app(proxies: int = 10) -> Flask:
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
    """Feed loader.

    Args:
        import_data (bool, optional): Whether to import data. Defaults to False.
    """
    feadloader = FeedLoader(FEED, os.environ.get("LIST_KEYS").split(","))
    if import_data or not os.path.exists(feadloader.feed.db_path):
        feadloader.nightly_import()
    if import_data or not os.path.exists(feadloader.GEOJSON_PATH):
        feadloader.geojson_exports()
    feadloader.run()


def run_dev_server(app: Flask = None, **kwargs) -> NoReturn:
    """Runs the dev server.

    Args:
        app (Flask, optional): Flask app. Defaults to None.
        kwargs: Keyword arguments for app.run.
    """

    threads = [Thread(target=feed_loader), Thread(target=app.run, **kwargs)]
    for thread in threads:
        thread.start()


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    feed_loader(True)
    # run_dev_server(create_default_app(), kwargs={"port": 80})
    # app = create_app("COMMUTER_RAIL")
    # app.run()
