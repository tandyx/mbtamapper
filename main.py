"""Main file for the project. Run this to start the backend of the project. \\
    User must produce the WSGI application using the create_default_app function."""

import argparse
import json
import logging

from flask import Flask, jsonify, redirect, render_template, request, url_for
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.middleware.proxy_fix import ProxyFix

from gtfs_loader import FeedLoader, Query
from helper_functions import limit_content_length

with open("route_keys.json", "r", encoding="utf-8") as file:
    KEY_DICT: dict[str, dict[str, str]] = json.load(file)
FEED_LOADER = FeedLoader(
    "https://cdn.mbta.com/MBTA_GTFS.zip",
    {k: v["route_types"] for k, v in KEY_DICT.items()},
)


def create_app(key: str, proxies: int = 5) -> Flask:
    """Create app for a given key

    Args:
        `key (str)`: Key for the app. Defaults to None.
        `proxies (int, optional)`: Number of proxies to allow on connection, default 10. \n
    Returns:
        `Flask`: app for the key."""
    _app = Flask(__name__)

    @_app.route("/")
    def render_map() -> str:
        """Returns map.html.

        returns:
            - `str`: map.html"""
        return render_template("map.html", navbar=KEY_DICT, **KEY_DICT[key])

    @_app.route("/vehicles")
    @_app.route("/api/vehicle")
    def get_vehicles() -> str:
        """Returns vehicles as geojson in the context of the route type AND \
            flask, exported to /vehicles as an api.
            
        Returns:
            - `str`: geojson of vehicles.
        """
        return jsonify(
            FEED_LOADER.get_vehicles_feature(
                key,
                Query(*KEY_DICT[key]["route_types"]),
                *request.args.get("include", "").split(","),
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
        return redirect(
            url_for(
                "static",
                filename=f"{FEED_LOADER.GEOJSON_FOLDER_NAME}/{key}/{FEED_LOADER.STOPS_FILE}",
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
        return redirect(
            url_for(
                "static",
                filename=f"{FEED_LOADER.GEOJSON_FOLDER_NAME}/{key}/{FEED_LOADER.PARKING_FILE}",
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

        return redirect(
            url_for(
                "static",
                filename=f"{FEED_LOADER.GEOJSON_FOLDER_NAME}/{key}/{FEED_LOADER.SHAPES_FILE}",
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
        - `proxies (int, optional)`: Number of proxies to allow on connection, default 10. \n
    Returns:
        - `Flask`: default app.
    """

    _app = Flask(__name__)

    @_app.route("/")
    def index():
        """Returns index.html."""

        return render_template("index.html", content=KEY_DICT)

    @limit_content_length(1024 * 1024)
    @_app.route("/api/<orm_name>")
    def get_orm(orm_name: str) -> str:
        """Returns the ORM for a given key.

        Args:
            - `orm (str)`: ORM to return.
        Returns:
            - `str`: ORM for the key.
        """
        orm_name = orm_name.lower()
        orm = next(
            (
                o
                for o in FEED_LOADER.REALTIME_ORMS + FEED_LOADER.SCHEDULE_ORMS
                if o.__name__.lower() == orm_name
            ),
            None,
        )
        if not orm:
            return jsonify({"error": f"{orm_name} not found."}), 404
        params = request.args.to_dict()
        include = params.pop("include", "").split(",")
        as_geojson = bool(params.pop("geojson", False))
        cols = orm.__table__.columns.keys()
        try:
            data = FEED_LOADER.get_orm_json(orm, *include, geojson=as_geojson, **params)
        except TimeoutError as error:
            logging.error(error)
            return jsonify({"error": str(error), f"args for {orm_name}": cols}), 408
        except Exception as error:  # pylint: disable=broad-except
            return jsonify({"error": str(error), f"args for {orm_name}": cols}), 400
        if data is None:
            return jsonify({"error": "no data", f"args for {orm_name}": cols}), 404
        return jsonify(data)

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
        {f"/{key}": create_app(key).wsgi_app for key in KEY_DICT},
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
        help="Logging level \\ (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )

    for key, value in kwargs.items():
        _argparse.add_argument(key, **value)

    return _argparse


# from gtfs_orms import Alert, Vehicle

if __name__ == "__main__":
    args = get_args().parse_args()
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    # FEED_LOADER.get_stop_features("commuter_rail", Query("2", "4"))
    if args.frontend:
        app = create_default_app(args.proxies)
        app.run(debug=True, port=args.port, host=args.host)
    else:
        FEED_LOADER.import_and_run(import_data=args.import_data)
