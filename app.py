# !/usr/bin/env python3

"""Main file for the project. Run this to start the backend of the project. \\ 
    User must produce the WSGI application using the create_default_app function.
    
see https://github.com/johan-cho/mbtamapper?tab=readme-ov-file#running

johan cho | 2023-2025

"""
import argparse
import difflib
import json
import logging
import os
import sys
import threading

import flask
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.middleware.proxy_fix import ProxyFix

from backend import FeedLoader, Query

LAYER_FOLDER: str = "geojsons"
with open(os.path.join("static", "config", "route_keys.json"), "r", -1, "utf-8") as f:
    KEY_DICT: dict[str, dict[str, str | list[str]]] = json.load(f)
FEED_LOADER: FeedLoader = FeedLoader(
    url="https://cdn.mbta.com/MBTA_GTFS.zip",
    geojson_path=os.path.join(os.getcwd(), "static", LAYER_FOLDER),
    keys_dict={k: v["route_types"] for k, v in KEY_DICT.items()},
)

logging.basicConfig(
    filename="main.log",
    filemode="a",
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.DEBUG,
)


def _error404(_app: flask.Flask, error: Exception | None = None) -> tuple[str, int]:
    """Returns 404.html // should only be used in the\
        context of a 404 error.

    Args:
        - `error (Exception)`: Error to log. \n
    Returns:
        - `tuple[str, int]`: 404.html and 404 status code.
    """
    if error:
        logging.error(error)
    _dict_field = "possible_url"
    url_dict = {"url": flask.request.url, "endpoint": flask.request.endpoint}
    logging.error("404: attempt to access %s", url_dict)
    for rule in _app.url_map.iter_rules():
        if not len(rule.defaults or ()) >= len(rule.arguments):
            continue
        url_for = flask.url_for(rule.endpoint)
        if difflib.SequenceMatcher(None, rule.endpoint, url_for).ratio() > 0.7:
            url_dict[_dict_field] = url_for
            break
    url_dict[_dict_field] = url_dict.get(_dict_field, "/")
    return flask.render_template("404.html", key_dict=KEY_DICT, **url_dict), 404


# def register_humanify(_app: flask.Flask, **kwargs) -> Humanify:
#     """registers humanify to the specified app

#     Args:
#         app (flask.Flask): pointer to the flask app.
#         kwargs: extra args to Humanify class

#     Returns:
#         Humanify: the registered object
#     """

#     humanify = Humanify(_app, challenge_type="one_click")
#     humanify.register_middleware(action="challenge", **kwargs)
#     return humanify


def create_key_app(key: str, proxies: int = 5) -> flask.Flask:
    """Create app for a given key

    Args:
        `key (str)`: Key for the app. Defaults to None.
        `proxies (int, optional)`: Number of proxies to allow on connection, default 10. \n
    Returns:
        `Flask`: app for the key."""
    _app = flask.Flask(__name__)

    @_app.route("/")
    def render_map() -> str:
        """Returns map.html.

        returns:
            - `str`: map.html"""
        return flask.render_template("map.html", navbar=KEY_DICT, **KEY_DICT[key])

    @_app.route("/key")
    def get_key() -> flask.Response:
        """Returns key.json.

        returns:
            - `Response`: the route key
        """
        return flask.jsonify(key)

    @_app.route("/vehicles")
    @_app.route("/api/vehicle")
    def get_vehicles() -> flask.Response:
        """Returns vehicles as geojson in the context of the route type AND \
            flask, exported to /vehicles as an api.
            
        Returns:
            - `Response`: geojson of vehicles.
        """
        return flask.jsonify(
            FEED_LOADER.get_vehicles_feature(
                key,
                Query(*KEY_DICT[key]["route_types"]),
                *[s.strip() for s in flask.request.args.get("include", "").split(",")],
            )
        )

    @_app.route("/stops")
    def get_stops() -> flask.Response:
        """Returns stops as geojson in the context of the route type AND \
            flask, exported to /stops as an api.
            
        returns:
            - `Response`: geojson of stops.
        """
        return _app.send_static_file(f"{LAYER_FOLDER}/{key}/{FEED_LOADER.STOPS_FILE}")

    @_app.route("/parking")
    @_app.route("/facilities")
    @_app.route("/api/parking")
    def get_parking() -> flask.Response:
        """Returns parking as geojson in the context of the route type AND \
            flask, exported to /parking as an api.
            
        returns:
            - `Response`: geojson of parking.
        """

        return _app.send_static_file(f"{LAYER_FOLDER}/{key}/{FEED_LOADER.PARKING_FILE}")

    @_app.route("/routes")
    @_app.route("/shapes")
    def get_routes() -> flask.Response:
        """Returns routes as geojson in the context of the route type AND \
            flask, exported to /routes as an api.
            
        returns:
            - `Response`: geojson of routes.
        """

        return _app.send_static_file(f"{LAYER_FOLDER}/{key}/{FEED_LOADER.SHAPES_FILE}")

    @_app.route("/favicon.ico")
    def favicon() -> flask.Response:
        """Returns favicon.ico.

        returns:
            - `Response`: favicon.ico.
        """
        return _app.send_static_file("img/all_routes.ico")

    @_app.teardown_appcontext
    def shutdown_session(exception: Exception | None = None) -> None:
        """Tears down database session.

        Args:
            - `exception (Exception, optional)`: Exception to log. Defaults to None.
        """
        FEED_LOADER.scoped_session.remove()
        if exception:
            logging.error(exception)

    @_app.errorhandler(404)
    def page_not_found(error: Exception | None = None) -> tuple[str, int]:
        """Returns 404.html.

        Args:
            - `error (Exception)`: Error to log.
        Returns:
            - `str`: 404.html.
        """
        return _error404(_app, error)

    if proxies:
        _app.wsgi_app = ProxyFix(
            _app.wsgi_app,
            x_for=proxies,
            x_proto=proxies,
            x_host=proxies,
            x_prefix=proxies,
        )
    return _app


def create_main_app(import_data: bool = False, proxies: int = 5) -> flask.Flask:
    """Creates the default Flask object

    args:
        - `import_data (bool, optional)`: Whether to import data. Defaults to False.
        - `proxies (int, optional)`: Number of proxies to allow on connection, default 10. \n
    returns:
        - `Flask`: default app.
    """

    _app = flask.Flask(__name__)

    # register_humanify(_app)

    with _app.app_context():  # background thread to run update
        thread = threading.Thread(
            target=FEED_LOADER.import_and_run, kwargs={"import_data": import_data}
        )
        thread.start()

    @_app.route("/")
    def index():
        """Returns index.html.

        returns:
            - `str`: index.html.
        """

        return flask.render_template("index.html", key_dict=KEY_DICT)

    @_app.route("/key_dict")
    def key_dict():
        """key dict json

        Returns:
            Response: the key dict
        """

        return flask.jsonify(KEY_DICT)

    @_app.teardown_appcontext
    def shutdown_session(exception: Exception | None = None) -> None:
        """Tears down database session.

        Args:
            - `exception (Exception, optional)`: Exception to log. Defaults to None.
        """
        FEED_LOADER.scoped_session.remove()
        if exception:
            logging.error(exception)

    @_app.route("/favicon.ico")
    def favicon() -> flask.Response:
        """returns favicon.ico

        returns:
            - `Response`: favicon.ico.
        """
        return _app.send_static_file("img/all_routes.ico")

    @_app.route("/sitemap.xml")
    def sitemap() -> flask.Response:
        """returns sitemap.xml

        returns:
            - `Response`: favicon.ico.
        """
        return _app.send_static_file("config/sitemap.xml")

    @_app.route("/api/<orm_name>")
    def orm_api(orm_name: str) -> tuple[str | flask.Response, int] | flask.Response:
        """Returns the ORM for a given key.

        Args:
            - `orm (str)`: ORM to return.\n
        Returns:
            - `str`: ORM for the key.
        """

        if not (orm := FeedLoader.find_orm(orm_name.strip().rstrip("s"))):
            return flask.jsonify({"error": f"{orm_name} not found."}), 400
        params = flask.request.args.to_dict()
        include = params.pop("include", "").split(",")
        params.pop("_", "")
        geojson = (
            bool(params.pop("geojson", False))  # this will be removed in the future
            or params.pop("file_type", "").lower() == "geojson"
        )
        timeout = 15  # seconds
        try:
            data = FEED_LOADER.timeout_get_orm_json(
                orm, *include, timeout=timeout, geojson=geojson, **params
            )
        except TimeoutError:
            return flask.jsonify({"error": f"response > {timeout}s"}), 408
        except Exception:  # pylint: disable=broad-except
            return flask.jsonify({"error": "?", f"{orm_name} args": orm.cols}), 400
        if data is None:
            return flask.jsonify({"error": "null", f"{orm_name} args": orm.cols}), 400
        return flask.jsonify(data)

    @_app.errorhandler(404)
    def page_not_found(error: Exception | None = None) -> tuple[str, int]:
        """Returns 404.html.

        Args:
            - `error (Exception)`: Error to log.\n
        Returns:
            - `str`: 404.html.
        """
        return _error404(_app, error)

    _app.wsgi_app = DispatcherMiddleware(
        _app.wsgi_app,
        {f"/{key}": create_key_app(key, proxies).wsgi_app for key in KEY_DICT},
    )

    return _app


def get_args(**kwargs) -> argparse.ArgumentParser:
    """Add arguments to the parser.

    args:
        - `**kwargs`: key value pairs of arguments to add to the parser.
            The key is the argument name and the value
            is a dictionary of arguments to pass to `add_argument`.\n
    returns:
        - `argparse.ArgumentParser`: parser with added arguments.
    """

    _argparse = argparse.ArgumentParser(description="Run the MBTA GTFS API server.")

    _argparse.add_argument(
        "--import_data",
        "-i",
        action="store_true",
        help="run import of database + export of geojson files",
    )
    _argparse.add_argument(
        "--port", "-p", type=int, default=5000, help="app.run() only: server port"
    )

    _argparse.add_argument(
        "--debug", "-d", action="store_true", help="app.run() only: debug mode"
    )

    _argparse.add_argument(
        "--host", default="127.0.0.1", help="app.run() only: server host address"
    )

    _argparse.add_argument(
        "--proxies",
        "-x",
        type=int,
        default=5,
        help="number of proxies to allow on connection.",
    )

    _argparse.add_argument(
        "--log_level",
        "-l",
        default="INFO",
        type=str,
        help="Logging level \\ (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )

    _argparse.add_argument(
        "--ssl_context",
        "--ssl",
        default=None,
        type=str,
        help="ssl context",
    )

    for key, value in kwargs.items():
        _argparse.add_argument(key, **value)

    return _argparse


# if __name__ == "__main__":
#     test = FEED_LOADER._get_orms(
#         "stoptime",
#         **{"stop_id": "MM-0023-S", "active": "True"},
#     )
#     # test[0][0].trip.calendar
#     print()


if __name__ == "__main__":
    args = get_args().parse_args()
    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(getattr(logging, args.log_level.upper()))
    if args.debug and (
        args.import_data or not FEED_LOADER.db_exists or not FEED_LOADER.geojsons_exist
    ):
        raise ValueError("cannot run in debug mode while importing data.")
    app = create_main_app(args.import_data, args.proxies)
    app.run(
        debug=args.debug, port=args.port, host=args.host, ssl_context=args.ssl_context
    )
