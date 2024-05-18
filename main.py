# !/usr/bin/env python3

"""Main file for the project. Run this to start the backend of the project. \\ 
    User must produce the WSGI application using the create_default_app function.
    
see https://github.com/johan-cho/mbtamapper?tab=readme-ov-file#running

"""

import argparse
import difflib
import json
import logging
import os

import flask
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.middleware.proxy_fix import ProxyFix

from gtfs_loader import FeedLoader, Query

STATIC_FOLDER: str = "static"
GEOJSON_FOLDER: str = "geojsons"
with open(
    os.path.join(STATIC_FOLDER, "config", "route_keys.json"), "r", encoding="utf-8"
) as file:
    KEY_DICT: dict[str, dict[str, str | list[str]]] = json.load(file)
FEED_LOADER: FeedLoader = FeedLoader(
    url="https://cdn.mbta.com/MBTA_GTFS.zip",
    geojson_path=os.path.join(os.getcwd(), STATIC_FOLDER, GEOJSON_FOLDER),
    keys_dict={k: v["route_types"] for k, v in KEY_DICT.items()},
)


def _error404(_app: flask.Flask, error: Exception = None) -> str:
    """Returns 404.html // should only be used in the\
        context of a 404 error.

    Args:
        - `error (Exception)`: Error to log. \n
    Returns:
        - `str`: 404.html.
    """
    if error:
        logging.error(error)
    _dict_field = "possible_url"
    url_dict = {"url": flask.request.url, "endpoint": flask.request.endpoint}
    for rule in _app.url_map.iter_rules():
        if not len(rule.defaults or ()) >= len(rule.arguments):
            continue
        url_for = flask.url_for(rule.endpoint)
        if difflib.SequenceMatcher(None, rule.endpoint, url_for).ratio() > 0.7:
            url_dict[_dict_field] = url_for
            break
    url_dict[_dict_field] = url_dict.get(_dict_field, "/")
    return flask.render_template("404.html", **url_dict), 404


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

    @_app.route("/vehicles")
    @_app.route("/api/vehicle")
    def get_vehicles() -> str:
        """Returns vehicles as geojson in the context of the route type AND \
            flask, exported to /vehicles as an api.
            
        Returns:
            - `str`: geojson of vehicles.
        """
        return flask.jsonify(
            FEED_LOADER.get_vehicles_feature(
                key,
                Query(*KEY_DICT[key]["route_types"]),
                *[s.strip() for s in flask.request.args.get("include", "").split(",")],
            )
        )

    @_app.route("/stops")
    @_app.route("/api/stop")
    def get_stops() -> str:
        """Returns stops as geojson in the context of the route type AND \
            flask, exported to /stops as an api.
            
        returns:
            - `str`: geojson of stops.
        """
        return flask.redirect(
            flask.url_for(
                "static", filename=f"{GEOJSON_FOLDER}/{key}/{FEED_LOADER.STOPS_FILE}"
            )
        )

    @_app.route("/parking")
    @_app.route("/facilities")
    @_app.route("/api/parking")
    def get_parking() -> str:
        """Returns parking as geojson in the context of the route type AND \
            flask, exported to /parking as an api.
            
        returns:
            - `str`: geojson of parking.
        """
        return flask.redirect(
            flask.url_for(
                "static", filename=f"{GEOJSON_FOLDER}/{key}/{FEED_LOADER.PARKING_FILE}"
            )
        )

    @_app.route("/routes")
    @_app.route("/shapes")
    @_app.route("/api/route")
    @_app.route("/api/shape")
    def get_routes() -> str:
        """Returns routes as geojson in the context of the route type AND \
            flask, exported to /routes as an api.
            
        returns:
            - `str`: geojson of routes.
        """

        return flask.redirect(
            flask.url_for(
                "static", filename=f"{GEOJSON_FOLDER}/{key}/{FEED_LOADER.SHAPES_FILE}"
            )
        )

    @_app.teardown_appcontext
    def shutdown_session(exception: Exception = None) -> None:
        """Tears down database session.

        Args:
            - `exception (Exception, optional)`: Exception to log. Defaults to None.
        """
        FEED_LOADER.scoped_session.remove()
        if exception:
            logging.error(exception)

    @_app.errorhandler(404)
    def page_not_found(error: Exception = None) -> str:
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


def create_default_app(proxies: int = 5) -> flask.Flask:
    """Creates the default Flask object

    Args:
        - `proxies (int, optional)`: Number of proxies to allow on connection, default 10. \n
    Returns:
        - `Flask`: default app.
    """

    _app = flask.Flask(__name__)

    @_app.route("/")
    def index():
        """Returns index.html.

        returns:
            - `str`: index.html.
        """

        return flask.render_template("index.html", content=KEY_DICT)

    @_app.route("/favicon.ico")
    def favicon() -> str:
        """Returns favicon.ico.

        returns:
            - `str`: favicon.ico.
        """
        return flask.send_from_directory(
            os.path.join(_app.root_path, "static", "img"), "all_routes.ico"
        )

    @_app.route("/api/<orm_name>")
    def get_orm(orm_name: str) -> str:
        """Returns the ORM for a given key.

        Args:
            - `orm (str)`: ORM to return.\n
        Returns:
            - `str`: ORM for the key.
        """

        if not (orm := FeedLoader.find_orm(orm_name)):
            return flask.jsonify({"error": f"{orm_name} not found."}), 400
        params = flask.request.args.to_dict()
        include = params.pop("include", "").split(",")
        geojson = bool(params.pop("geojson", False))
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
    def page_not_found(error: Exception = None) -> str:
        """Returns 404.html.

        Args:
            - `error (Exception)`: Error to log.\n
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
        help="Import data from GTFS feed.",
    )

    _argparse.add_argument(
        "--frontend",
        "-f",
        action="store_true",
        # default=True,
        help="Run flask ONLY - overrides --import_data.",
    )

    _argparse.add_argument(
        "--port",
        "-p",
        type=int,
        default=80,
        help="Port to run the server on.",
    )

    _argparse.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to run the server on.",
    )

    _argparse.add_argument(
        "--proxies",
        "-x",
        type=int,
        default=5,
        help="Number of proxies to allow on connection.",
    )

    _argparse.add_argument(
        "--log_level",
        "-l",
        default="INFO",
        type=str,
        help="Logging level \\ (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )

    for key, value in kwargs.items():
        _argparse.add_argument(key, **value)

    return _argparse


# from gtfs_orms import Alert, Vehicle

if __name__ == "__main__":
    args = get_args().parse_args()
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
    # FEED_LOADER.get_shape_features("subway", Query("1", "0"))
    # FEED_LOADER.get_stop_features("commuter_rail", Query("2", "4"))
    # FEED_LOADER.get_orm_json(StopTime, stop_id="70061")
    # args.frontend = True
    if args.frontend:
        app = create_default_app(args.proxies)
        app.run(debug=True, port=args.port, host=args.host)
    else:
        FEED_LOADER.import_and_run(import_data=args.import_data)
