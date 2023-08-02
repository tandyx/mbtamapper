"""Flask app for MBTA GTFS data."""
# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
import os
from geojson import FeatureCollection

from flask import Flask, render_template, jsonify
from sqlalchemy.exc import OperationalError
from gtfs_loader import Feed, Query
from gtfs_realtime import *


class FlaskApp:
    """Flask app for MBTA GTFS data.

    Attributes:
        app (Flask): Flask app
        feed_obj (Feed): GTFS feed
        key (str): key for route types
    """

    SILVER_LINE_ROUTES = "741,742,743,751,749,746"

    def __init__(self, app: Flask, feed_obj: Feed, key: str = None):
        self.app = app
        self.feed = feed_obj
        self.key = key or "ALL_ROUTES"
        self.route_types = os.environ.get(key)
        self.query = Query(self.route_types.split(","))
        self._setup_routes()

    def __repr__(self) -> str:
        return f"<FlaskApp(key={self.key}, feed={self.feed})>"

    def _setup_routes(self):
        """Sets up the app routes."""
        self.app.route("/")(self.render_map)
        self.app.route("/value")(self.get_value)
        self.app.route("/vehicles")(self.get_vehicles)
        self.app.teardown_appcontext(self.shutdown_session)

    def render_map(self):
        """Returns index.html."""
        return render_template("map.html")

    def render_index(self):
        """Returns index.html."""
        return render_template("index.html")

    def get_value(self):
        """Returns value of KEY."""
        return self.key

    def get_vehicles(self):
        """Returns vehicles as geojson."""
        sess = self.feed.scoped_session()
        query = self.query.return_vehicles_query(
            self.SILVER_LINE_ROUTES if self.key == "RAPID_TRANSIT" else ""
        )
        self.feed.import_realtime()
        try:
            data: list[tuple[Vehicle]] = sess.execute(query).all()
        except OperationalError:
            data = []
        geojson_features = [v[0].as_feature() for v in data]
        return jsonify(FeatureCollection(geojson_features))

    # pylint: disable=unused-argument
    def shutdown_session(self, exception=None) -> None:
        """Tears down database session."""
        self.feed.scoped_session.remove()

    def run(self, **options) -> None:
        """Runs the app."""
        self.app.run(**options)
